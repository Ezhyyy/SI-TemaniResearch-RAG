import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, text
from .extensions import db

def create_app():
    base_dir = Path(__file__).resolve().parents[1]
    load_dotenv(base_dir / ".env")

    app = Flask(__name__)

    # Default to MySQL, fallback to SQLite if MySQL fails
    mysql_uri = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:@localhost:3306/temaniresearch?charset=utf8mb4"
    )
    sqlite_uri = "sqlite:///" + str(base_dir / "temani_research.db")

    # Uji koneksi ke database yang ditentukan
    chosen_db_uri = mysql_uri
    try:
        test_engine = create_engine(mysql_uri)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logging.info("✅ Database: Terhubung ke MySQL.")
    except Exception as e:
        logging.warning(
            f"⚠️ MySQL belum siap ({e}). Menggunakan fallback SQLite: {sqlite_uri}"
        )
        chosen_db_uri = sqlite_uri

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "temaniresearch-secret-2026"),
        SQLALCHEMY_DATABASE_URI=chosen_db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=str(base_dir / "uploads"),
        CHROMA_PATH=str(base_dir / "chroma_db"),
        MAX_CONTENT_LENGTH=int(os.getenv("MAX_PDF_SIZE_MB", "20")) * 1024 * 1024,
        MAX_RETRIEVAL_DISTANCE=float(os.getenv("MAX_RETRIEVAL_DISTANCE", "0.90")),
        JWT_EXPIRES_HOURS=int(os.getenv("JWT_EXPIRES_HOURS", "24")),
        GEMINI_API_KEY=os.getenv("GEMINI_API_KEY", ""),
        GEMINI_CHAT_MODEL=os.getenv("GEMINI_CHAT_MODEL", "gemini-3.5-flash-lite"),
        GEMINI_EMBEDDING_MODEL=os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"),
    )

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["CHROMA_PATH"]).mkdir(parents=True, exist_ok=True)

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    db.init_app(app)

    with app.app_context():
        # Buat tabel otomatis jika belum ada
        db.create_all()

    from .routes import api
    app.register_blueprint(api, url_prefix="/api")

    @app.get("/")
    def index():
        return {
            "status": "online",
            "service": "TemaniResearch API",
            "model_llm": app.config["GEMINI_CHAT_MODEL"],
            "model_embedding": app.config["GEMINI_EMBEDDING_MODEL"]
        }

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "TemaniResearch API"}

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(error="Ukuran file melebihi batas maksimum 20MB."), 413

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify(error="Endpoint tidak ditemukan."), 404

    @app.errorhandler(Exception)
    def unexpected_error(error):
        app.logger.exception("Kesalahan server: %s", error)
        return jsonify(error="Terjadi kesalahan pada server."), 500

    return app
