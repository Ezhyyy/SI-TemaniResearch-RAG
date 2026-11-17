import os
import sys
import unittest
import pymupdf as fitz

# Pastikan path backend masuk ke sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models import User, Document

class TestTemaniResearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_01_health_and_root(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["service"], "TemaniResearch API")
        self.assertEqual(data["model_llm"], "gemini-3.5-flash-lite")
        print("✅ 1. Health & Root API: PASSED")

    def test_02_login_admin_and_user(self):
        # Login Admin
        res_admin = self.client.post("/api/auth/login", json={
            "email": "admin@temaniresearch.ac.id",
            "password": "Admin123!"
        })
        self.assertEqual(res_admin.status_code, 200)
        admin_data = res_admin.get_json()
        self.assertIn("token", admin_data)
        self.__class__.admin_token = admin_data["token"]

        # Login User
        res_user = self.client.post("/api/auth/login", json={
            "email": "mahasiswa@temaniresearch.ac.id",
            "password": "User123!"
        })
        self.assertEqual(res_user.status_code, 200)
        user_data = res_user.get_json()
        self.assertIn("token", user_data)
        self.__class__.user_token = user_data["token"]
        print("✅ 2. Login Admin & User: PASSED")

    def test_03_upload_and_index_pdf(self):
        # Buat PDF dummy 3 halaman dengan PyMuPDF
        pdf_path = "sample_paper.pdf"
        doc = fitz.open()

        # Halaman 1
        p1 = doc.new_page()
        p1.insert_text(
            (50, 100),
            "Judul: Penerapan Sistem RAG untuk Analisis Jurnal Ilmiah.\n"
            "Penulis: Tim Peneliti TemaniResearch.\n"
            "Tahun: 2026.\n"
            "Abstrak: Penelitian ini mengembangkan sistem informasi cerdas berbasis RAG untuk membantu mahasiswa."
        )

        # Halaman 2
        p2 = doc.new_page()
        p2.insert_text(
            (50, 100),
            "Metodologi Penelitian:\n"
            "Metode yang digunakan adalah ekstraksi teks per halaman menggunakan PyMuPDF. "
            "Setiap halaman di-chunk menjadi potongan 350 kata dengan overlap 40 kata. "
            "Model embedding yang digunakan adalah gemini-embedding-001 yang disimpan di ChromaDB."
        )

        # Halaman 3
        p3 = doc.new_page()
        p3.insert_text(
            (50, 100),
            "Hasil dan Pembahasan:\n"
            "Eksperimen membuktikan bahwa integrasi ChromaDB dan Gemini 3.5 Flash Lite "
            "menghasilkan kecepatan respon rata-rata 1.2 detik dan sitasi halaman akurat pada 95% uji coba."
        )

        doc.save(pdf_path)
        doc.close()

        # Upload oleh Admin sebagai dokumen PUBLIK
        with open(pdf_path, "rb") as f:
            data = {
                "title": "Penerapan Sistem RAG untuk Analisis Jurnal Ilmiah",
                "authors": "Tim Peneliti TemaniResearch",
                "year": "2026",
                "category": "Artificial Intelligence",
                "description": "Jurnal pengujian RAG dengan Gemini API",
                "visibility": "public",
                "file": (open(pdf_path, "rb"), "sample_paper.pdf")
            }
            res = self.client.post(
                "/api/documents/upload",
                headers={"Authorization": f"Bearer {self.admin_token}"},
                data=data,
                content_type="multipart/form-data"
            )

        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        self.assertEqual(res.status_code, 201)
        resp_json = res.get_json()
        self.assertEqual(resp_json["document"]["status"], "ready")
        self.assertEqual(resp_json["document"]["page_count"], 3)
        self.__class__.document_id = resp_json["document"]["id"]
        print(f"✅ 3. Upload & Vector Indexing PDF (ID: {self.document_id}): PASSED")

    def test_04_rag_chat_and_citations(self):
        # User bertanya mengenai metodologi pada dokumen yang diunggah
        res = self.client.post(
            f"/api/documents/{self.document_id}/chat",
            headers={"Authorization": f"Bearer {self.user_token}"},
            json={"question": "Metode apa yang digunakan untuk ekstraksi teks pada penelitian ini?"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("answer", data)
        self.assertIn("sources", data)
        self.assertTrue(len(data["sources"]) > 0)
        # Pastikan sumber mencantumkan nomor halaman
        pages = [s["page_number"] for s in data["sources"]]
        print(f"✅ 4. RAG Chatbot with Citations (Halaman Rujukan: {pages}): PASSED")

    def test_05_summary(self):
        res = self.client.get(
            f"/api/documents/{self.document_id}/summary",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("summary", data)
        print("✅ 5. Structured AI Summary: PASSED")

    def test_06_user_personal_library_upload(self):
        # Buat PDF pribadi untuk user biasa
        pdf_path = "personal_note.pdf"
        doc = fitz.open()
        p = doc.new_page()
        p.insert_text((50, 100), "Catatan Riset Pribadi Mahasiswa: Fokus pada perbandingan model embedding.")
        doc.save(pdf_path)
        doc.close()

        with open(pdf_path, "rb") as f:
            data = {
                "title": "Catatan Riset Pribadi Mahasiswa",
                "authors": "Mahasiswa",
                "year": "2026",
                "category": "Notes",
                "visibility": "private",
                "file": (open(pdf_path, "rb"), "personal_note.pdf")
            }
            res = self.client.post(
                "/api/documents/upload",
                headers={"Authorization": f"Bearer {self.user_token}"},
                data=data,
                content_type="multipart/form-data"
            )

        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        self.assertEqual(res.status_code, 201)
        doc_data = res.get_json()["document"]
        self.assertEqual(doc_data["visibility"], "private")
        print(f"✅ 6. User Personal Library Upload (Private ID: {doc_data['id']}): PASSED")

if __name__ == "__main__":
    unittest.main()
