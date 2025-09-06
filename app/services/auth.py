# app/services/auth.py
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from typing import Optional, Dict, Any
from sqlalchemy import text
from ..db.engine import SessionLocal
from ..models.user import RoleEnum, AccessLevelEnum
import os
import re

# ---- JWT config ----
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable is not set")
JWT_ALGORITHM = "HS256"

# ---- Email validation ----
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$", re.I)

def _norm_email(v: Optional[str]) -> str:
    return (v or "").strip().lower()

def _assert_valid_email(email: str) -> None:
    if not EMAIL_RE.fullmatch(email):
        # normalized, API-friendly message your routes can map to 400
        raise ValueError("invalid_email")

class AuthService:
    # ---------- password helpers ----------
    @staticmethod
    def hash_password(password: str) -> str:
        return generate_password_hash(password)

    @staticmethod
    def verify_password(hashed_password: str, password: str) -> bool:
        return check_password_hash(hashed_password, password)

    # ---------- JWT helpers ----------
    @staticmethod
    def generate_token(user_id: int, email: str, role: str) -> str:
        payload = {
            "user_id": user_id,
            "email": email,
            "role": role,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload if valid."""
        try:
            if not token:
                return None
            if token.startswith("Bearer "):
                token = token[7:]
            return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, AttributeError):
            return None

    # ---------- user flows ----------
    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data if successful."""
        if not email or not password:
            return None
        email = _norm_email(email)
        if not EMAIL_RE.fullmatch(email):
            return None

        with SessionLocal() as session:
            row = session.execute(
                text("SELECT * FROM users WHERE email = :email"),
                {"email": email},
            ).mappings().first()

            if not row or not AuthService.verify_password(row["password_hash"], password):
                return None

            return dict(row)

    @staticmethod
    def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user account (admin only)."""
        with SessionLocal() as session:
            email = _norm_email(user_data.get("email"))
            _assert_valid_email(email)

            # duplicate email?
            existing_user = session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email},
            ).scalar()
            if existing_user:
                # API-friendly message your routes can map to 409
                raise ValueError("email_exists")

            # validate role
            try:
                role = RoleEnum(user_data["role"])
            except Exception:
                raise ValueError("invalid_role")

            # validate access level
            try:
                access_level = AccessLevelEnum(
                    user_data.get("default_access_level", "view")
                )
            except Exception:
                raise ValueError("invalid_access_level")

            password = user_data.get("password") or ""
            if not password:
                raise ValueError("invalid_password")

            password_hash = AuthService.hash_password(password)

            result = session.execute(
                text(
                    """
                    INSERT INTO users (email, password_hash, role, name, default_access_level)
                    VALUES (:email, :password_hash, :role, :name, :default_access_level)
                    RETURNING id, email, role, name, default_access_level, created_at
                    """
                ),
                {
                    "email": email,
                    "password_hash": password_hash,
                    "role": role.value,
                    "name": user_data.get("name"),
                    "default_access_level": access_level.value,
                },
            )
            new_user = result.mappings().first()
            session.commit()
            return dict(new_user)

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        with SessionLocal() as session:
            row = session.execute(
                text(
                    """
                    SELECT id, email, role, name, default_access_level, created_at, updated_at
                    FROM users
                    WHERE id = :user_id
                    """
                ),
                {"user_id": user_id},
            ).mappings().first()
            return dict(row) if row else None

    @staticmethod
    def get_all_users() -> list:
        with SessionLocal() as session:
            rows = session.execute(
                text(
                    """
                    SELECT id, email, role, name, default_access_level, created_at, updated_at
                    FROM users
                    ORDER BY created_at DESC
                    """
                )
            ).mappings().all()
            return [dict(r) for r in rows]

    @staticmethod
    def update_user(user_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with SessionLocal() as session:
            exists = session.execute(
                text("SELECT 1 FROM users WHERE id = :id"),
                {"id": user_id},
            ).scalar()
            if not exists:
                return None

            # normalize + validate fields
            params: Dict[str, Any] = {"user_id": user_id}
            sets = []

            if "email" in update_data:
                email = _norm_email(update_data["email"])
                _assert_valid_email(email)
                sets.append("email = :email")
                params["email"] = email

            if "name" in update_data:
                sets.append("name = :name")
                params["name"] = update_data["name"]

            if "role" in update_data:
                try:
                    RoleEnum(update_data["role"])
                except Exception:
                    raise ValueError("invalid_role")
                sets.append("role = :role")
                params["role"] = update_data["role"]

            if "default_access_level" in update_data:
                try:
                    AccessLevelEnum(update_data["default_access_level"])
                except Exception:
                    raise ValueError("invalid_access_level")
                sets.append("default_access_level = :default_access_level")
                params["default_access_level"] = update_data["default_access_level"]

            if not sets:
                raise ValueError("no_fields_to_update")

            q = f"""
                UPDATE users
                SET {", ".join(sets)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = :user_id
                RETURNING id, email, role, name, default_access_level, created_at, updated_at
            """
            res = session.execute(text(q), params).mappings().first()
            session.commit()
            return dict(res) if res else None

    @staticmethod
    def is_admin(user_id: int) -> bool:
        with SessionLocal() as session:
            role = session.execute(
                text("SELECT role FROM users WHERE id = :id"),
                {"id": user_id},
            ).scalar()
            return role == RoleEnum.Admin.value if role else False
