import json
import logging
from typing import List, Dict, Any, Tuple
from app.services.pdf_service import PDFService
from app.services.gemini_service import gemini_service
from app.services.vector_service import vector_service

logger = logging.getLogger("uvicorn.error")

class RAGService:
    @staticmethod
    def process_and_index_document(document_id: int, file_path: str) -> bool:
        """
        Alur lengkap pengindeksan PDF:
        1. Ekstrak teks per halaman
        2. Chunking teks dengan tetap menyimpan info halaman
        3. Embedding tiap chunk via Gemini API
        4. Simpan ke database vektor ChromaDB
        """
        try:
            pages = PDFService.extract_text_with_pages(file_path)
            if not pages:
                logger.error(f"Dokumen {document_id} kosong atau tidak ada teks yang dapat diekstrak.")
                return False

            chunks = PDFService.chunk_pages(pages, chunk_size=350, overlap=40)
            if not chunks:
                return False

            embeddings = []
            for c in chunks:
                emb = gemini_service.embed_text(c["text"])
                embeddings.append(emb)

            vector_service.add_document_chunks(document_id, chunks, embeddings)
            logger.info(f"✅ Dokumen {document_id} berhasil diindeks ({len(chunks)} chunks).")
            return True
        except Exception as e:
            logger.error(f"❌ Gagal mengindeks dokumen {document_id}: {e}")
            return False

    @staticmethod
    def answer_question(
        document_id: int,
        document_title: str,
        question: str,
        history: List[Dict[str, str]] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Alur RAG Chatbot:
        1. Embed pertanyaan
        2. Cari chunk paling relevan dari ChromaDB
        3. Bangun prompt berkonteks kuat
        4. Kirim ke LLM (gemini-3.5-flash-lite)
        5. Kembalikan jawaban + list sitasi halaman
        """
        # 1. Embed query
        query_emb = gemini_service.embed_query(question)

        # 2. Retrieve top-5 chunks
        relevant_chunks = vector_service.search_chunks(document_id, query_emb, top_k=5)

        if not relevant_chunks:
            return (
                "Dokumen ini belum selesai diproses atau tidak memiliki konten teks yang dapat ditelusuri.",
                []
            )

        # 3. Format konteks
        context_str = ""
        citations = []
        seen_pages = set()

        for chunk in relevant_chunks:
            p = chunk["page"]
            context_str += f"\n--- [Kutipan dari Halaman {p}] ---\n{chunk['text']}\n"
            if p not in seen_pages:
                seen_pages.add(p)
                citations.append({
                    "page": p,
                    "source": document_title,
                    "snippet": chunk["text"][:160] + "..."
                })

        # Urutkan sitasi berdasarkan nomor halaman
        citations.sort(key=lambda x: x["page"])

        system_instruction = (
            "Anda adalah asisten AI penelitian bernama 'TemaniResearch'. "
            "Tugas Anda adalah menjawab pertanyaan pengguna BERDASARKAN HANYA pada konteks kutipan dokumen yang diberikan. "
            "Aturan wajib:\n"
            "1. Jawab dalam Bahasa Indonesia yang baku, jelas, dan akademis.\n"
            "2. Selalu sebutkan nomor halaman rujukan di dalam kalimat jawaban Anda (contoh: 'Berdasarkan Halaman 3...').\n"
            "3. Jika informasi TIDAK ADA atau TIDAK DAPAT DISIMPULKAN dari kutipan dokumen yang diberikan, "
            "Anda WAJIB menjawab: 'Informasi ini tidak ditemukan dalam dokumen.' Jangan mengarang atau berhalusinasi.\n"
            "4. Jangan menggunakan pengetahuan umum di luar teks yang diberikan."
        )

        # History multi-turn
        history_str = ""
        if history:
            for msg in history[-4:]:  # Ambil 2 turn terakhir
                role_label = "Pengguna" if msg.get("role") == "user" else "Asisten"
                history_str += f"{role_label}: {msg.get('content')}\n"

        prompt = f"""Judul Dokumen: {document_title}

Konteks Dokumen yang Relevan:
{context_str}

Riwayat Percakapan Sebelumnya:
{history_str}

Pertanyaan Pengguna Saat Ini:
{question}

Silakan jawab pertanyaan di atas sesuai aturan dan sebutkan nomor halaman rujukan:"""

        response_text = gemini_service.generate_chat_response(prompt, system_instruction)
        return response_text, citations

    @staticmethod
    def generate_summary(document_id: int, document_title: str) -> str:
        """
        Menghasilkan ringkasan dokumen 4 aspek (Tujuan, Metodologi, Temuan Utama, Kesimpulan).
        """
        # Ambil chunk awal dan akhir dokumen untuk ringkasan menyeluruh
        intro_emb = gemini_service.embed_query("pendahuluan latar belakang tujuan penelitian abstract")
        findings_emb = gemini_service.embed_query("hasil pembahasan temuan kesimpulan saran conclusion")

        intro_chunks = vector_service.search_chunks(document_id, intro_emb, top_k=3)
        findings_chunks = vector_service.search_chunks(document_id, findings_emb, top_k=3)

        combined_texts = []
        for c in intro_chunks + findings_chunks:
            combined_texts.append(f"(Halaman {c['page']}) {c['text']}")

        context_str = "\n\n".join(combined_texts)

        prompt = f"""Berikut adalah kutipan teks penting dari dokumen penelitian '{document_title}':

{context_str}

Buatlah ringkasan eksekutif penelitian ini dalam Bahasa Indonesia yang terstruktur rapi dengan 4 bagian berikut:
1. 🎯 **Tujuan Penelitian**: Apa masalah utama dan target yang ingin dicapai?
2. 🔬 **Metodologi**: Metode atau pendekatan apa yang digunakan?
3. 📊 **Temuan Utama**: Apa hasil kunci atau data penting yang ditemukan?
4. 💡 **Kesimpulan & Implikasi**: Apa kesimpulan akhir dan manfaat praktisnya?

Gunakan format bullet points dan sebutkan estimasi halaman jika terdapat di kutipan."""

        system_instruction = (
            "Anda adalah analis jurnal ilmiah. Sajikan ringkasan yang objektif, padat, dan mudah dipahami mahasiswa."
        )

        return gemini_service.generate_chat_response(prompt, system_instruction)

rag_service = RAGService()
