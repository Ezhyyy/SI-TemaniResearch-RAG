Project ini adalah tugas akhir dari Mata Kuliah Sistem Informasi berbasis AI. Saya ingin membuat sebuah Sistem Informasi berbasis AI yang sederhana. Dimana bisa mengunggah PDF, lalu AI bisa menjawab pertanyaan berdasarkan PDF yang diunggah.

# Konsep project

**TemaniResearch** adalah sistem informasi berbasis AI untuk membantu pengguna membaca, memahami, dan menelusuri koleksi dokumen penelitian. Admin mengelola satu basis data/repository dokumen PDF. Pengguna dapat membuka Research Library, memilih dokumen, meminta ringkasan AI, dan berdiskusi melalui chatbot yang menjawab berdasarkan isi dokumen terpilih.

Nilai utama sistem adalah jawaban AI yang dapat ditelusuri: setiap jawaban penting menampilkan sumber dokumen dan nomor halaman yang relevan.

# Latar belakang

Mahasiswa dan peneliti sering membutuhkan waktu lama untuk menemukan informasi inti dalam artikel, laporan, atau skripsi. Membaca dokumen PDF secara linear tidak selalu efisien, sementara pencarian kata kunci biasa sering tidak memahami konteks pertanyaan. Di sisi lain, penggunaan AI generatif tanpa sumber yang jelas berisiko menghasilkan jawaban yang tidak dapat diverifikasi.

TemaniResearch memadukan repository dokumen terpusat dengan Retrieval-Augmented Generation (RAG). Sistem mengambil potongan teks yang relevan dari dokumen sebelum AI menyusun jawaban, sehingga pengguna memperoleh informasi yang lebih kontekstual, disertai rujukan halaman untuk pemeriksaan mandiri.

## Rumusan masalah

1. Bagaimana menyediakan repository penelitian yang rapi dan mudah dikelola oleh admin? 
2. Bagaimana membantu pengguna memahami isi PDF secara cepat melalui ringkasan dan tanya-jawab berbahasa alami?
3. Bagaimana memastikan jawaban AI merujuk pada dokumen dan halaman yang relevan?
4. Bagaimana menyimpan riwayat percakapan agar pengguna dapat melanjutkan eksplorasi dokumen?

## Tujuan

1. Membangun sistem repository dokumen PDF dengan metadata yang dikelola admin.
2. Mengimplementasikan chatbot RAG untuk menjawab pertanyaan berdasarkan dokumen yang dipilih pengguna.
3. Menyediakan ringkasan AI untuk mempercepat pemahaman dokumen.
4. Menampilkan referensi sumber dan halaman pada hasil AI.
5. Menyediakan riwayat chat per pengguna dan dokumen.