from datetime import datetime, timedelta, timezone
from functools import wraps
import jwt
from flask import current_app, g, jsonify, request
from .extensions import db
from .models import User

def issue_token(user):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "name": user.name,
        "email": user.email,
        "iat": now,
        "exp": now + timedelta(hours=current_app.config.get("JWT_EXPIRES_HOURS", 24))
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

def require_auth(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                return jsonify(error="Autentikasi diperlukan. Silakan login."), 401
            token = header[7:]
            try:
                payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
                user = db.session.get(User, int(payload["sub"]))
            except (jwt.InvalidTokenError, KeyError, ValueError):
                return jsonify(error="Token tidak valid atau sudah kedaluwarsa."), 401
            if not user:
                return jsonify(error="Pengguna tidak ditemukan."), 401
            if role and user.role != role:
                return jsonify(error=f"Akses khusus {role}."), 403
            g.current_user = user
            return view(*args, **kwargs)
        return wrapped
    return decorator
