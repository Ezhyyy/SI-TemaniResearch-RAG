import os
import shutil
import sys

# Tambahkan backend ke sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models import User

def reset_database(clean_files=True):
    print("=" * 50)
    print("🧹 MEMULAI PROSES RESET DATABASE (START FROM 0)")
    print("=" * 50)

    app = create_app()

    with app.app_context():
        # 1. Nonaktifkan foreign key checks sementara untuk truncate bersih
        print("1. Mengosongkan tabel MySQL...")
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0;"))
        
        tables = ["chat_messages", "documents", "users"]
        for table in tables:
            db.session.execute(db.text(f"TRUNCATE TABLE `{table}`;"))
            print(f"   - Tabel `{table}` berhasil dikosongkan (AUTO_INCREMENT kembali ke 1)")
            
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.session.commit()
        print("   ✅ Semua tabel MySQL telah bersih.")

        # 2. Bersihkan file PDF fisik & ChromaDB (jika diaktifkan)
        if clean_files:
            upload_dir = app.config.get("UPLOAD_FOLDER", "uploads")
            chroma_dir = app.config.get("CHROMA_PATH", "./chroma_db")

            print("\n2. Membersihkan penyimpanan file & vector store...")
            if os.path.exists(upload_dir):
                for item in os.listdir(upload_dir):
                    if item == ".gitkeep":
                        continue
                    item_path = os.path.join(upload_dir, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                print(f"   - Folder upload ({upload_dir}) dikosongkan.")

            try:
                import chromadb
                chroma = chromadb.PersistentClient(path=chroma_dir)
                chroma.delete_collection("temaniresearch_chunks")
                print("   - Collection ChromaDB dihapus.")
            except Exception:
                pass

            if os.path.exists(chroma_dir):
                try:
                    shutil.rmtree(chroma_dir)
                    os.makedirs(chroma_dir, exist_ok=True)
                    print(f"   - Folder vector ChromaDB ({chroma_dir}) di-reset.")
                except Exception:
                    pass
            print("   ✅ File uploads dan ChromaDB bersih.")

        # 3. Buat kembali akun default TemaniResearch
        print("\n3. Membuat akun bawaan baru (Seed Akun Awal)...")
        admin = User(
            name="Administrator TemaniResearch",
            email="admin@temaniresearch.ac.id",
            role="admin",
        )
        admin.set_password("Admin123!")

        mahasiswa = User(
            name="Mahasiswa Peneliti",
            email="mahasiswa@temaniresearch.ac.id",
            role="user",
        )
        mahasiswa.set_password("User123!")

        db.session.add(admin)
        db.session.add(mahasiswa)
        db.session.commit()

        print(f"   - Admin dibuat: {admin.email} (ID: {admin.id})")
        print(f"   - User dibuat : {mahasiswa.email} (ID: {mahasiswa.id})")

    print("\n" + "=" * 50)
    print("🎉 RESET SELESAI! Database & File siap digunakan dari 0.")
    print("=" * 50)

if __name__ == "__main__":
    reset_database()
