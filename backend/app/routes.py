import os
import uuid
from pathlib import Path
from flask import Blueprint, current_app, g, jsonify, request, send_from_directory
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from .auth import issue_token, require_auth
from .extensions import db
from .models import ChatMessage, Document, User
from .rag import RagError, index_document, summarize_document, answer_question, delete_document_index

api = Blueprint("api", __name__)
ALLOWED_EXTENSION = {"pdf"}

def _json():
    return request.get_json(silent=True) or {}

@api.post("/auth/register")
def register():
    data = _json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or len(password) < 6:
        return jsonify(error="Nama, email valid, dan password minimal 6 karakter wajib diisi."), 400

    if User.query.filter_by(email=email).first():
        return jsonify(error="Email sudah terdaftar. Silakan login."), 409

    # User pertama otomatis jadi admin
    total_users = User.query.count()
    role = "admin" if total_users == 0 else "user"

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify(token=issue_token(user), user=user.public()), 201

@api.post("/auth/login")
def login():
    data = _json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify(error="Email atau password salah."), 401

    return jsonify(token=issue_token(user), user=user.public())

@api.get("/auth/me")
@require_auth()
def me():
    return jsonify(user=g.current_user.public())

@api.get("/documents")
@require_auth()
def documents():
    query_str = request.args.get("q", "").strip()
    visibility_filter = request.args.get("visibility", "").strip()
    category_filter = request.args.get("category", "").strip()
    year_filter = request.args.get("year", "").strip()

    stmt = Document.query.filter(Document.status != "archived")

    # Kontrol akses:
    # Dokumen publik bisa diakses semua user yang login
    # Dokumen privat HANYA bisa diakses oleh pembuatnya (atau admin)
    if g.current_user.role != "admin":
        stmt = stmt.filter(
            or_(
                Document.visibility == "public",
                (Document.visibility == "private") & (Document.uploaded_by == g.current_user.id)
            )
        )

    if visibility_filter in ["public", "private"]:
        stmt = stmt.filter(Document.visibility == visibility_filter)

    if category_filter:
        stmt = stmt.filter(Document.category.ilike(f"%{category_filter}%"))

    if year_filter and year_filter.isdigit():
        stmt = stmt.filter(Document.year == int(year_filter))

    if query_str:
        needle = f"%{query_str}%"
        stmt = stmt.filter(
            or_(
                Document.title.ilike(needle),
                Document.authors.ilike(needle),
                Document.category.ilike(needle),
                Document.keywords.ilike(needle)
            )
        )

    results = stmt.order_by(Document.created_at.desc()).all()
    return jsonify(documents=[doc.public() for doc in results])

@api.get("/documents/<int:document_id>")
@require_auth()
def document_detail(document_id):
    document = db.session.get(Document, document_id)
    if not document or document.status == "archived":
        return jsonify(error="Dokumen tidak ditemukan."), 404

    if document.visibility == "private" and document.uploaded_by != g.current_user.id and g.current_user.role != "admin":
        return jsonify(error="Dokumen ini bersifat privat."), 403

    return jsonify(document=document.public(detail=True))

@api.get("/documents/<int:document_id>/file")
@require_auth()
def document_file(document_id):
    document = db.session.get(Document, document_id)
    if not document or document.status == "archived":
        return jsonify(error="Dokumen tidak ditemukan."), 404

    if document.visibility == "private" and document.uploaded_by != g.current_user.id and g.current_user.role != "admin":
        return jsonify(error="Dokumen ini bersifat privat."), 403

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        document.stored_filename,
        as_attachment=False,
        download_name=document.original_filename
    )

@api.post("/documents/upload")
@require_auth()
def upload_document():
    upload = request.files.get("file")
    title = request.form.get("title", "").strip()

    if not upload or not upload.filename or not title:
        return jsonify(error="File PDF dan judul dokumen wajib diisi."), 400

    ext = upload.filename.rsplit(".", 1)[-1].lower() if "." in upload.filename else ""
    if ext not in ALLOWED_EXTENSION:
        return jsonify(error="Hanya file berekstensi .pdf yang diperbolehkan."), 400

    # User biasa upload sebagai "private" secara default (atau boleh pilih jika diizinkan)
    # Admin bisa memilih "public" atau "private"
    req_visibility = request.form.get("visibility", "public" if g.current_user.role == "admin" else "private")
    if g.current_user.role != "admin" and req_visibility == "public":
        req_visibility = "private"  # User biasa private

    stored_filename = f"{uuid.uuid4().hex}_{secure_filename(upload.filename)}"
    destination = Path(current_app.config["UPLOAD_FOLDER"]) / stored_filename
    upload.save(destination)

    year = request.form.get("year", "").strip()
    year_int = int(year) if year.isdigit() else None

    document = Document(
        title=title,
        authors=request.form.get("authors", "").strip() or None,
        year=year_int,
        category=request.form.get("category", "").strip() or None,
        description=request.form.get("description", "").strip() or None,
        keywords=request.form.get("keywords", "").strip() or None,
        original_filename=upload.filename,
        stored_filename=stored_filename,
        status="processing",
        visibility=req_visibility,
        uploaded_by=g.current_user.id,
    )
    db.session.add(document)
    db.session.commit()

    # Indexing PDF
    try:
        pages, chunks = index_document(document, destination)
        document.status = "ready"
        document.page_count = pages
        db.session.commit()
    except Exception as error:
        current_app.logger.exception("Gagal mengindeks %s: %s", destination, error)
        document.status = "failed"
        document.processing_error = str(error)
        db.session.commit()
        return jsonify(error=f"Gagal mengindeks dokumen: {error}", document=document.public(detail=True)), 500

    return jsonify(document=document.public(detail=True)), 201

@api.delete("/documents/<int:document_id>")
@require_auth()
def delete_document(document_id):
    document = db.session.get(Document, document_id)
    if not document:
        return jsonify(error="Dokumen tidak ditemukan."), 404

    if document.uploaded_by != g.current_user.id and g.current_user.role != "admin":
        return jsonify(error="Anda tidak berhak menghapus dokumen ini."), 403

    # Hapus vector dari ChromaDB
    delete_document_index(document.id)

    # Hapus file fisik
    target = Path(current_app.config["UPLOAD_FOLDER"]) / document.stored_filename
    if target.exists():
        try:
            target.unlink()
        except Exception:
            pass

    # Hapus pesan chat terkait dokumen ini terlebih dahulu
    ChatMessage.query.filter_by(document_id=document.id).delete()

    db.session.delete(document)
    db.session.commit()
    return jsonify(message="Dokumen dan indeks vektor berhasil dihapus.")

@api.get("/documents/<int:document_id>/summary")
@require_auth()
def get_summary(document_id):
    document = db.session.get(Document, document_id)
    if not document or document.status == "archived":
        return jsonify(error="Dokumen tidak ditemukan."), 404

    if document.visibility == "private" and document.uploaded_by != g.current_user.id and g.current_user.role != "admin":
        return jsonify(error="Dokumen ini bersifat privat."), 403

    if document.status != "ready":
        return jsonify(error="Dokumen belum siap untuk diringkas."), 400

    if document.summary:
        return jsonify(summary=document.summary, cached=True)

    try:
        summary = summarize_document(document)
        document.summary = summary
        db.session.commit()
        return jsonify(summary=summary, cached=False)
    except RagError as error:
        return jsonify(error=str(error)), 400

@api.post("/documents/<int:document_id>/chat")
@require_auth()
def chat_document(document_id):
    document = db.session.get(Document, document_id)
    if not document or document.status == "archived":
        return jsonify(error="Dokumen tidak ditemukan."), 404

    if document.visibility == "private" and document.uploaded_by != g.current_user.id and g.current_user.role != "admin":
        return jsonify(error="Dokumen ini bersifat privat."), 403

    if document.status != "ready":
        return jsonify(error="Dokumen belum selesai diindeks."), 400

    question = _json().get("question", "").strip()
    if not question:
        return jsonify(error="Pertanyaan wajib diisi."), 400

    # Ambil riwayat chat sebelumnya
    prev_chats = ChatMessage.query.filter_by(
        user_id=g.current_user.id,
        document_id=document.id
    ).order_by(ChatMessage.created_at.asc()).all()

    history = []
    for c in prev_chats:
        history.append({"role": "user", "content": c.question})
        history.append({"role": "assistant", "content": c.answer})

    try:
        answer, sources = answer_question(document, question, history=history)
    except RagError as error:
        return jsonify(error=str(error)), 400

    chat = ChatMessage(
        user_id=g.current_user.id,
        document_id=document.id,
        question=question,
        answer=answer,
        sources_json=sources
    )
    db.session.add(chat)
    db.session.commit()

    return jsonify(
        chat_id=chat.id,
        question=question,
        answer=answer,
        sources=sources
    )

@api.get("/documents/<int:document_id>/chats")
@require_auth()
def list_chats(document_id):
    document = db.session.get(Document, document_id)
    if not document:
        return jsonify(error="Dokumen tidak ditemukan."), 404

    chats = ChatMessage.query.filter_by(
        user_id=g.current_user.id,
        document_id=document.id
    ).order_by(ChatMessage.created_at.asc()).all()

    return jsonify(messages=[c.public() for c in chats])

@api.get("/stats")
@require_auth()
def stats():
    total_docs = Document.query.filter(Document.status == "ready").count()
    public_docs = Document.query.filter(Document.status == "ready", Document.visibility == "public").count()
    personal_docs = Document.query.filter(Document.status == "ready", Document.visibility == "private").count()
    total_users = User.query.count()

    return jsonify(
        total_documents=total_docs,
        public_documents=public_docs,
        personal_documents=personal_docs,
        total_users=total_users
    )
