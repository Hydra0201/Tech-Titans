from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, g
from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from psycopg.errors import UniqueViolation
import re
import jwt

from .. import get_conn

admin_users_bp = Blueprint("admin_users", __name__)
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALLOWED_ROLES = {"Admin", "Employee", "Client", "Consultant"}
ALLOWED_ACCESS = {"view", "edit"}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$", re.I)

def _clean_email(v: str | None) -> str:
    return (v or "").strip().lower()

def _norm_role(v: str | None) -> str:
    v = (v or "").strip()
    return (v[:1].upper() + v[1:].lower()) if v else ""

def _norm_access(v: str | None) -> str:
    return (v or "view").strip().lower()

def _get_bearer_token() -> str | None:
    auth = request.headers.get("Authorization", "")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    return auth.split(None, 1)[1]

def _decode_jwt(token: str) -> dict | None:
    """Decode HS256 JWT using app config; return payload or None."""
    if not token:
        return None
    secret = current_app.config.get("JWT_SECRET")
    if not secret:
        # Misconfiguration; treat as unauthorized rather than 500
        return None
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

@admin_users_bp.post("/admin/users")
def create_user():
    """
    POST /admin/users — create a user.
    Body: { name, email, password, role, default_access_level }
    Returns:
      201 { user }
      400 { error: bad_request | invalid_email }
      401 { error: unauthorized }
      403 { error: forbidden }
      409 { error: email_exists }
      500 { error: server_error }
    """

    # ---------- JWT guard: require valid token with Admin role ----------
    token = _get_bearer_token()
    payload = _decode_jwt(token)
    if not payload:
        return jsonify({"error": "unauthorized"}), 401

    # token format aligns with your login route: {"sub": str(id), "role": "...", ...}
    role = payload.get("role")
    if role != "Admin":
        return jsonify({"error": "forbidden"}), 403

    g.user_id = payload.get("sub")
    g.user_role = role
    g.user_email = payload.get("email")
    # -------------------------------------------------------------------

    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip() or None
    email = _clean_email(data.get("email"))
    password = data.get("password") or ""
    role = _norm_role(data.get("role"))
    default_access = _norm_access(data.get("default_access_level"))

    # Required fields & allowed values
    if (not email) or (not password) or (role not in ALLOWED_ROLES) or (default_access not in ALLOWED_ACCESS):
        return jsonify({
            "error": "bad_request",
            "hint": {
                "required": ["email", "password", "role"],
                "role_allowed": sorted(ALLOWED_ROLES),
                "default_access_level_allowed": sorted(ALLOWED_ACCESS),
            },
        }), 400

    # Email format validation
    if not EMAIL_RE.fullmatch(email):
        return jsonify({"error": "invalid_email"}), 400

    pw_hash = pwd_ctx.hash(password)

    with get_conn() as conn:
        tx = conn.begin() if not conn.in_transaction() else conn.begin_nested()
        try:
            row = conn.execute(
                text("""
                    INSERT INTO users (email, name, role, default_access_level, password_hash)
                    VALUES (:email, :name, :role, :access, :hash)
                    RETURNING id, email, name, role, default_access_level, created_at
                """),
                {"email": email, "name": name, "role": role, "access": default_access, "hash": pw_hash},
            ).mappings().one()

            user = dict(row)
            if isinstance(user.get("created_at"), datetime):
                user["created_at"] = user["created_at"].isoformat()

            tx.commit()
            return jsonify({"user": user}), 201

        except IntegrityError as e:
            if tx.is_active:
                tx.rollback()
            orig = getattr(e, "orig", None)
            sqlstate = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
            if isinstance(orig, UniqueViolation) or sqlstate == "23505":
                return jsonify({"error": "email_exists"}), 409
            current_app.logger.exception("create_user failed (integrity)")
            return jsonify({"error": "server_error"}), 500

        except Exception:
            if tx.is_active:
                tx.rollback()
            current_app.logger.exception("create_user failed")
            return jsonify({"error": "server_error"}), 500
