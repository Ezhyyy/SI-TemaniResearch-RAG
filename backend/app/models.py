from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from .extensions import db

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("admin", "user"), nullable=False, default="user")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, name=None, email=None, role="user", **kwargs):
        super().__init__(**kwargs)
        if name is not None:
            self.name = name
        if email is not None:
            self.email = email
        if role is not None:
            self.role = role
        for key, value in kwargs.items():
            setattr(self, key, value)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def public(self):
        return {"id": self.id, "name": self.name, "email": self.email, "role": self.role}


class Document(db.Model):
    __tablename__ = "documents"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    authors = db.Column(db.String(500), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    category = db.Column(db.String(120), nullable=True)
    description = db.Column(db.Text, nullable=True)
    keywords = db.Column(db.String(500), nullable=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    page_count = db.Column(db.Integer, nullable=True)
    status = db.Column(db.Enum("processing", "ready", "failed", "archived"), nullable=False, default="processing")
    visibility = db.Column(db.Enum("public", "private"), nullable=False, default="public")
    processing_error = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def public(self, detail=False):
        data = {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "category": self.category,
            "keywords": self.keywords,
            "page_count": self.page_count,
            "status": self.status,
            "visibility": self.visibility,
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at.isoformat(),
        }
        if detail:
            data.update({
                "description": self.description,
                "original_filename": self.original_filename,
                "processing_error": self.processing_error,
                "has_summary": bool(self.summary),
                "summary": self.summary
            })
        return data


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=False, index=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    sources_json = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def public(self):
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "sources": self.sources_json,
            "created_at": self.created_at.isoformat(),
            "document_id": self.document_id
        }
