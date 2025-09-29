# app/routes/auth.py
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import text
from passlib.context import CryptContext
from werkzeug.security import check_password_hash as wz_check  # <- add
import jwt

from .. import get_conn

# make sure this blueprint ends up under /api so FE hits /api/auth/login
auth_bp = Blueprint("auth", __name__, url_prefix="/api")  # <- add url_prefix here or when registering
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _norm_email(v: str | None) -> str:
    return (v or "").strip().lower()

def _jwt_encode(payload: dict) -> str:
    secret = current_app.config.get("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET not configured")
    return jwt.encode(payload, secret, algorithm="HS256")

def _verify_password(password: str, stored_hash: str) -> bool:
    """
    Accept both bcrypt ($2b$...) and Werkzeug PBKDF2 ('pbkdf2:sha256:...') hashes.
    """
    if not stored_hash:
        return False
    try:
        if stored_hash.startswith("$2"):  # bcrypt family
            return pwd_ctx.verify(password, stored_hash)
        if stored_hash.startswith("pbkdf2:"):
            return wz_check(stored_hash, password)
        # last-chance attempt with passlib (may support other legacy formats)
        return pwd_ctx.verify(password, stored_hash)
    except Exception:
        return False

@auth_bp.post("/auth/login")
def login():
    """
    POST /api/auth/login
    Body: { "email": str, "password": str }
    Returns: 200 { "access_token": <jwt>, "user": { id, email, name, role, default_access_level } }
             400 on missing fields, 401 on bad credentials
    """
    data = request.get_json(silent=True) or {}
    email = _norm_email(data.get("email"))
    password = data.get("password") or ""
    if not email or not password:
        return {"error": "bad_request", "message": "email and password required"}, 400

    # ensure connection is closed/returned to pool
    with get_conn() as conn:  # <- context manager
        row = conn.execute(
            text("""
                SELECT id, email, name, role, default_access_level, password_hash
                FROM users
                WHERE lower(email) = :email
                LIMIT 1
            """),
            {"email": email},
        ).mappings().one_or_none()

    if not row or not _verify_password(password, row["password_hash"]):
        return {"error": "invalid_credentials"}, 401

    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=int(current_app.config.get("JWT_EXPIRES_HOURS", 24)))

    token = _jwt_encode({
    "sub": str(row["id"]),   # 🔑 store as string
    "email": row["email"],
    "role": row["role"],
    "iat": int(now.timestamp()),
    "exp": int(exp.timestamp()),
    })

    user = {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"],
        "role": row["role"],
        "default_access_level": row["default_access_level"],
    }
    return jsonify({"access_token": token, "user": user}), 200
