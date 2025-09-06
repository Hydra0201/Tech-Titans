# app/routes/auth.py
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import text
from passlib.context import CryptContext
import jwt

from .. import get_conn

auth_bp = Blueprint("auth", __name__)
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _norm_email(v: str | None) -> str:
    return (v or "").strip().lower()

def _jwt_encode(payload: dict) -> str:
    secret = current_app.config.get("JWT_SECRET")
    if not secret:
        # keep it explicit so failures are clear during dev/tests
        raise RuntimeError("JWT_SECRET not configured")
    return jwt.encode(payload, secret, algorithm="HS256")

@auth_bp.post("/auth/login")
def login():
    """
    POST /auth/login — verify email/password and issue a JWT.

    Body: { "email": str, "password": str }
    Returns: 200 { "access_token": <jwt>, "user": { id, email, name, role, default_access_level } }
             400 on missing fields, 401 on bad credentials
    """
    data = request.get_json(silent=True) or {}
    email = _norm_email(data.get("email"))
    password = data.get("password") or ""
    if not email or not password:
        return {"error": "bad_request", "message": "email and password required"}, 400

    conn = get_conn()
    row = conn.execute(
        text("""
            SELECT id, email, name, role, default_access_level, password_hash
            FROM users
            WHERE lower(email) = :email
            LIMIT 1
        """),
        {"email": email},
    ).mappings().one_or_none()

    if not row or not pwd_ctx.verify(password, row["password_hash"]):
        return {"error": "invalid_credentials"}, 401

    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=int(current_app.config.get("JWT_EXPIRES_HOURS", 24)))

    token = _jwt_encode({
        "sub": row["id"],
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
