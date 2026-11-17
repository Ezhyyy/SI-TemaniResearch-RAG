import os
import time
import logging
from typing import List, Optional
from app.config import settings

logger = logging.getLogger("uvicorn.error")

class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        self.chat_model_name = settings.GEMINI_CHAT_MODEL
        self.embedding_model_name = settings.GEMINI_EMBEDDING_MODEL
        self._init_client()

    def _init_client(self):
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.warning("⚠️ GEMINI_API_KEY belum disetel. AI Service berjalan dalam Mock/Offline mode.")
            self.client = None
            return

        try:
            # Menggunakan Google Generative AI SDK
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai
            logger.info("✅ Gemini API Client berhasil diinisialisasi.")
        except Exception as e:
            logger.error(f"❌ Gagal inisialisasi Gemini Client: {e}")
            self.client = None

    def embed_text(self, text: str, max_retries: int = 3) -> List[float]:
        """
        Menghasilkan representasi vektor dari teks menggunakan model embedding.
        """
        if not self.client:
            # Dummy embedding 768 dimensi untuk testing tanpa API key
            import hashlib
            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            return [((hash_val >> (i % 32)) & 0xFF) / 255.0 for i in range(768)]

        for attempt in range(max_retries):
            try:
                # Coba embed dengan nama model embedding yang ditentukan
                model_path = f"models/{self.embedding_model_name}"
                res = self.client.embed_content(
                    model=model_path,
                    content=text,
                    task_type="retrieval_document"
                )
                return res["embedding"]
            except Exception as e:
                err_msg = str(e).lower()
                # Jika model tidak ditemukan, coba fallback ke text-embedding-004
                if "not found" in err_msg and self.embedding_model_name != "text-embedding-004":
                    try:
                        res = self.client.embed_content(
                            model="models/text-embedding-004",
                            content=text,
                            task_type="retrieval_document"
                        )
                        return res["embedding"]
                    except Exception:
                        pass
                if "429" in str(e) or "quota" in err_msg:
                    time.sleep(2 * (attempt + 1))
                else:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(1)
        raise RuntimeError("Gagal menghasilkan embedding setelah percobaan ulang.")

    def embed_query(self, query: str) -> List[float]:
        """
        Embedding khusus untuk query pencarian user.
        """
        if not self.client:
            import hashlib
            hash_val = int(hashlib.md5(query.encode()).hexdigest(), 16)
            return [((hash_val >> (i % 32)) & 0xFF) / 255.0 for i in range(768)]

        try:
            model_path = f"models/{self.embedding_model_name}"
            res = self.client.embed_content(
                model=model_path,
                content=query,
                task_type="retrieval_query"
            )
            return res["embedding"]
        except Exception:
            # Fallback jika model embedding baru belum tersedia di region user
            res = self.client.embed_content(
                model="models/text-embedding-004",
                content=query,
                task_type="retrieval_query"
            )
            return res["embedding"]

    def generate_chat_response(self, prompt: str, system_instruction: str = "") -> str:
        """
        Menghasilkan jawaban chat/ringkasan menggunakan model LLM.
        """
        if not self.client:
            return (
                "*[Mode Demo / Offline]* GEMINI_API_KEY belum disetel di `.env`.\n\n"
                "Konteks terdeteksi dengan sukses. Silakan tambahkan GEMINI_API_KEY gratis dari "
                "Google AI Studio (https://aistudio.google.com/) untuk mendapatkan jawaban AI asli."
            )

        models_to_try = [
            self.chat_model_name,
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b"
        ]

        last_error = None
        for model_name in models_to_try:
            try:
                gen_model = self.client.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction if system_instruction else None
                )
                response = gen_model.generate_content(prompt)
                return response.text
            except Exception as e:
                last_error = e
                logger.warning(f"Gagal memanggil model {model_name}: {e}. Mencoba model alternatif...")
                continue

        raise RuntimeError(f"Semua model generative gagal merespon: {last_error}")

gemini_service = GeminiService()
