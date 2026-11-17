import hashlib
from collections import OrderedDict
import chromadb
import pymupdf as fitz
from flask import current_app
from google import genai
from .text_processing import chunk_text

class RagError(Exception):
    pass

_client_instance = None
_client_key = None

def _client():
    global _client_instance, _client_key
    key = current_app.config.get("GEMINI_API_KEY", "")
    if not key or key == "your_gemini_api_key_here":
        return None  # Demo / offline mode
    if _client_instance is None or _client_key != key:
        _client_instance = genai.Client(api_key=key)
        _client_key = key
    return _client_instance

_chroma_client = None
_chroma_path = None

def _collection():
    global _chroma_client, _chroma_path
    path = current_app.config.get("CHROMA_PATH", "./chroma_db")
    if _chroma_client is None or _chroma_path != path:
        _chroma_client = chromadb.PersistentClient(path=path)
        _chroma_path = path
    return _chroma_client.get_or_create_collection(
        name="temaniresearch_chunks", metadata={"hnsw:space": "cosine"}
    )

def extract_pdf_pages(pdf_path):
    try:
        pdf = fitz.open(pdf_path)
        pages = [{"page_number": idx + 1, "text": page.get_text("text").strip()}
                 for idx, page in enumerate(pdf)]
        pdf.close()
    except Exception as error:
        raise RagError(f"PDF tidak dapat dibaca: {error}") from error
    pages = [page for page in pages if page["text"]]
    if not pages:
        raise RagError("PDF tidak mengandung teks digital yang dapat diekstrak.")
    return pages

def embed_texts(texts):
    client = _client()
    if client is None:
        # Mock embedding 768 dimensi jika belum ada API key
        vectors = []
        for text in texts:
            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            vec = [((hash_val >> (i % 32)) & 0xFF) / 255.0 for i in range(768)]
            vectors.append(vec)
        return vectors

    model_name = current_app.config.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    try:
        response = client.models.embed_content(
            model=model_name,
            contents=texts
        )
        return [item.values for item in response.embeddings]
    except Exception as error:
        # Fallback jika model embedding baru belum didukung region
        try:
            response = client.models.embed_content(
                model="text-embedding-004",
                contents=texts
            )
            return [item.values for item in response.embeddings]
        except Exception:
            raise RagError(f"Embedding Gemini gagal: {error}") from error

def index_document(document, pdf_path):
    pages = extract_pdf_pages(pdf_path)
    records = []
    for page in pages:
        for chunk_index, content in enumerate(chunk_text(page["text"])):
            records.append((page["page_number"], chunk_index, content))
    if not records:
        raise RagError("Tidak ada chunk teks yang dibuat dari PDF.")

    collection = _collection()
    # Hapus vector lama jika ada
    try:
        collection.delete(where={"document_id": document.id})
    except Exception:
        pass

    # Batch embedding agar tidak kena rate limit
    for start in range(0, len(records), 30):
        batch = records[start:start + 30]
        vectors = embed_texts([record[2] for record in batch])
        collection.add(
            ids=[f"doc-{document.id}-p-{page}-c-{chunk}" for page, chunk, _ in batch],
            embeddings=vectors,
            documents=[content for _, _, content in batch],
            metadatas=[{
                "document_id": document.id,
                "document_title": document.title,
                "page_number": page,
                "chunk_index": chunk
            } for page, chunk, _ in batch],
        )
    return len(pages), len(records)

def delete_document_index(document_id):
    try:
        _collection().delete(where={"document_id": int(document_id)})
    except Exception:
        pass

def retrieve(document_id, question, count=5):
    query_vector = embed_texts([question])[0]
    result = _collection().query(
        query_embeddings=[query_vector],
        n_results=count,
        where={"document_id": document_id},
        include=["documents", "metadatas", "distances"]
    )
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    dists = result.get("distances", [[]])[0]

    max_distance = current_app.config.get("MAX_RETRIEVAL_DISTANCE", 0.90)
    hits = []
    for doc, meta, dist in zip(docs, metas, dists):
        if dist is not None and dist > max_distance:
            continue
        hits.append({
            "text": doc,
            "page_number": meta.get("page_number", 1),
            "document_title": meta.get("document_title", ""),
            "distance": dist
        })
    return hits

def summarize_document(document):
    client = _client()
    if client is None:
        return (
            "*[Mode Demo]* Ringkasan belum dapat digenerate secara otomatis karena GEMINI_API_KEY belum disetel.\n\n"
            "1. 🎯 **Tujuan Penelitian**: Eksplorasi sistem informasi AI.\n"
            "2. 🔬 **Metodologi**: Pendekatan RAG terpadu.\n"
            "3. 📊 **Temuan Utama**: Sitasi halaman berhasil dipetakan.\n"
            "4. 💡 **Kesimpulan**: Siap digunakan untuk tugas akhir."
        )

    # Ambil kutipan representatif
    intro_hits = retrieve(document.id, "tujuan penelitian latar belakang pendahuluan abstract", count=3)
    method_hits = retrieve(document.id, "metode penelitian analisis algoritma dataset", count=3)
    finding_hits = retrieve(document.id, "hasil pembahasan temuan utama kesimpulan saran", count=3)

    combined = OrderedDict()
    for item in intro_hits + method_hits + finding_hits:
        key = (item["page_number"], item["text"])
        combined[key] = item

    if not combined:
        raise RagError("Tidak cukup konteks dokumen untuk membuat ringkasan.")

    context_lines = [f"[Halaman {item['page_number']}]\n{item['text']}" for item in combined.values()]
    prompt = f"""Anda adalah asisten AI penelitian ilmiah 'TemaniResearch'.
Tugas Anda adalah membuat ringkasan eksekutif terstruktur dari dokumen '{document.title}'.

Konteks Dokumen:
{chr(10).join(context_lines)}

Format keluaran WAJIB Bahasa Indonesia rapi dengan 4 bagian:
1. 🎯 **Tujuan Penelitian**: Masalah inti dan objektif yang ingin dicapai.
2. 🔬 **Metodologi**: Pendekatan, metode, atau dataset yang digunakan.
3. 📊 **Temuan Utama**: Temuan kunci atau hasil penting yang didapatkan.
4. 💡 **Kesimpulan & Implikasi**: Kesimpulan akhir dan manfaat praktisnya.

Buat secara objektif, padat, dan sertakan rujukan halaman jika disebutkan dalam konteks."""

    model_name = current_app.config.get("GEMINI_CHAT_MODEL", "gemini-3.5-flash-lite")
    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text
    except Exception as error:
        raise RagError(f"Generasi ringkasan gagal: {error}") from error

def answer_question(document, question, history=None):
    client = _client()
    hits = retrieve(document.id, question, count=5)

    if not hits:
        return "Informasi ini tidak ditemukan dalam dokumen.", []

    sources = []
    seen = set()
    for item in hits:
        key = (item["page_number"], item["text"][:100])
        if key not in seen:
            seen.add(key)
            sources.append({
                "document_title": document.title,
                "page_number": item["page_number"],
                "snippet": item["text"][:160] + "..."
            })
    sources.sort(key=lambda s: s["page_number"])

    if client is None:
        source_pages = ", ".join(f"hlm. {s['page_number']}" for s in sources)
        return (
            f"*[Mode Demo - GEMINI_API_KEY belum disetel]*\n\n"
            f"Konteks ditemukan pada {source_pages}. "
            f"Pertanyaan Anda: '{question}'. "
            f"Silakan isi GEMINI_API_KEY di backend/.env untuk respon AI asli.",
            sources
        )

    context_lines = [f"[Halaman {item['page_number']}]\n{item['text']}" for item in hits]

    history_text = ""
    if history:
        for msg in history[-4:]:
            role_label = "Pengguna" if msg.get("role") == "user" else "Asisten"
            history_text += f"{role_label}: {msg.get('content')}\n"

    prompt = f"""Judul Dokumen: {document.title}

Konteks Dokumen:
{chr(10).join(context_lines)}

Riwayat Percakapan:
{history_text}

Pertanyaan:
{question}

Instruksi:
1. Jawab HANYA berdasarkan konteks di atas.
2. Selalu sebutkan rujukan halaman di awal atau akhir jawaban (misal: 'Berdasarkan Halaman 2...').
3. Jika informasi TIDAK DITEMUKAN dalam konteks, jawab PERSIS: 'Informasi ini tidak ditemukan dalam dokumen.'
4. Jawab dalam Bahasa Indonesia yang santun dan akademis."""

    model_name = current_app.config.get("GEMINI_CHAT_MODEL", "gemini-3.5-flash-lite")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return response.text, sources
    except Exception as error:
        raise RagError(f"Gagal menghasilkan jawaban: {error}") from error
