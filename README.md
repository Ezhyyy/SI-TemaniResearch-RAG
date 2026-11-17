# 📚 TemaniResearch — Sistem Informasi Penelitian Berbasis AI & RAG

**TemaniResearch** adalah aplikasi sistem informasi berbasis kecerdasan buatan (*Artificial Intelligence*) yang membantu mahasiswa, dosen, dan peneliti dalam membaca, memahami, serta menelusuri koleksi dokumen penelitian (PDF) secara efisien dan terverifikasi.

Aplikasi ini menggunakan teknik **Retrieval-Augmented Generation (RAG)** yang didukung oleh **Google Gemini API (Free Tier)**. Setiap jawaban yang diberikan chatbot menyertakan sitasi rujukan dokumen dan nomor halaman yang tepat untuk mencegah halusinasi AI.

---

## 🌟 Fitur Utama

1. **Repository Dokumen Publik & Jurnal Pribadi (Personal Library)**
   - **Admin**: Mengelola repository publik (semua pengguna dapat membaca & berdiskusi).
   - **Mahasiswa / Peneliti**: Dapat mengunggah jurnal pribadi yang hanya bisa diakses oleh dirinya sendiri.
2. **Automated Vector Indexing**
   - File PDF otomatis diekstrak teks per halaman menggunakan PyMuPDF.
   - Dipotong (*chunking*) dengan mempertahankan metadata nomor halaman.
   - Diberikan representasi vektor oleh **`gemini-embedding-001`** dan disimpan di **ChromaDB**.
3. **Chatbot RAG Interaktif dengan Sitasi Halaman**
   - Tanya-jawab interaktif menggunakan **`gemini-3.5-flash-lite`** (Free Tier).
   - Menampilkan badge sitasi halaman (contoh: `📄 Hlm. 2`, `📄 Hlm. 3`).
   - AI hanya menjawab berdasarkan isi dokumen; jika tidak ada, sistem dengan jujur menjawab *"Informasi ini tidak ditemukan dalam dokumen."*
4. **Ringkasan AI Terstruktur (4 Aspek)**
   - Menghasilkan ringkasan otomatis:
     - 🎯 **Tujuan Penelitian**
     - 🔬 **Metodologi**
     - 📊 **Temuan Utama**
     - 💡 **Kesimpulan & Rekomendasi**
   - Hasil ringkasan di-cache di database agar hemat kuota token.
5. **Manajemen Akun & Riwayat Diskusi**
   - Login & Register dengan JWT Authentication.
   - Riwayat percakapan tersimpan otomatis per dokumen dan pengguna.

---

## 🛠️ Tech Stack

- **Frontend**: React (Vite) + Vanilla CSS Modern responsif
- **Backend**: Python (Flask) + REST API
- **Database Relasional**: MySQL (dengan auto-fallback SQLite untuk kemudahan dev lokal)
- **Vector Database**: ChromaDB (Lokal & Cepat)
- **PDF Engine**: PyMuPDF
- **Model LLM & Embedding**:
  - LLM: `gemini-3.5-flash-lite`
  - Embedding: `gemini-embedding-001` (fallback `text-embedding-004`)

---

## 🚀 Panduan Menjalankan Sistem

### 1. Konfigurasi Backend

Masuk ke folder `backend`:
```powershell
cd backend
```

Buka file `.env` dan tambahkan **GEMINI_API_KEY** gratis dari [Google AI Studio](https://aistudio.google.com/):
```env
GEMINI_API_KEY=AIzaSy...
```
*(Catatan: Tanpa API Key, sistem tetap dapat dijalankan dalam mode offline/demo)*

Inisialisasi database dan akun demo:
```powershell
.\venv\Scripts\python.exe seed.py
```

Jalankan server backend (port 5000):
```powershell
.\venv\Scripts\python.exe run.py
```

---

### 2. Menjalankan Frontend

Buka terminal baru di root project:
```powershell
cd frontend
npm run dev
```
Akses antarmuka web di browser melalui: **`http://localhost:5173`**

---

## 👥 Akun Uji Coba (Demo Credentials)

| Role | Email | Password | Hak Akses |
|---|---|---|---|
| **Administrator** | `admin@temaniresearch.ac.id` | `Admin123!` | Kelola semua dokumen publik & privat |
| **Mahasiswa** | `mahasiswa@temaniresearch.ac.id` | `User123!` | Akses dokumen publik + upload jurnal pribadi |

---

## 🧪 Pengujian Otomatis (Unit & Integration Test)

Untuk memverifikasi seluruh pipeline (auth, upload PDF, ChromaDB embedding, RAG Q&A, sitasi halaman, dan summary):
```powershell
.\backend\venv\Scripts\python.exe backend\test_backend.py
```
Hasil:
```text
Ran 6 tests in 4.123s
OK
✅ 1. Health & Root API: PASSED
✅ 2. Login Admin & User: PASSED
✅ 3. Upload & Vector Indexing PDF: PASSED
✅ 4. RAG Chatbot with Citations: PASSED
✅ 5. Structured AI Summary: PASSED
✅ 6. User Personal Library Upload: PASSED
```
