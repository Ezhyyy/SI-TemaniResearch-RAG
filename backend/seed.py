import os
import sys

# Pastikan folder backend masuk ke sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():
    # Buat akun admin jika belum ada
    admin = User.query.filter_by(email="admin@temaniresearch.ac.id").first()
    if not admin:
        admin = User(name="Administrator", email="admin@temaniresearch.ac.id", role="admin")
        admin.set_password("Admin123!")
        db.session.add(admin)
        print("✅ Akun Admin berhasil dibuat: admin@temaniresearch.ac.id / Admin123!")

    # Buat akun user demo jika belum ada
    user = User.query.filter_by(email="mahasiswa@temaniresearch.ac.id").first()
    if not user:
        user = User(name="Mahasiswa Peneliti", email="mahasiswa@temaniresearch.ac.id", role="user")
        user.set_password("User123!")
        db.session.add(user)
        print("✅ Akun User demo berhasil dibuat: mahasiswa@temaniresearch.ac.id / User123!")

    db.session.commit()
    print("🚀 Inisialisasi database selesai.")
