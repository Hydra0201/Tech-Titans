# app/routes/auth.py

# POST /auth/login — Authenticate a user (no JWT).
# - Body: { "email": str, "password": str }
# - Effect: Looks up `users` by email, verifies bcrypt password_hash.
# - Returns: 200 { "user": { id, email, name, role, default_access_level } }
# - Errors: 400 bad_request (missing fields), 401 invalid_credentials
# - Notes: No token is issued; front-end should store user state client-side or
#          you can later switch to cookie/JWT without changing this signature.
# - Tables touched: users

from flask import Blueprint, request, jsonify
from sqlalchemy import text
from passlib.context import CryptContext

from .. import get_conn

auth_bp = Blueprint("auth", __name__)
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _norm_email(v: str | None) -> str:
    return (v or "").strip().lower()

@auth_bp.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email = _norm_email(data.get("email"))
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "bad_request", "message": "email and password required"}), 400

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

    # invalid email or wrong password
    if not row or not pwd_ctx.verify(password, row["password_hash"]):
        return jsonify({"error": "invalid_credentials"}), 401

    user = {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "default_access_level": row.get("default_access_level"),
    }
    return jsonify({"user": user}), 200
