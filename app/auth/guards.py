# app/auth/guards.py
from __future__ import annotations
from functools import wraps
from typing import Iterable, Optional
from flask import request, jsonify, current_app, g
import jwt
from sqlalchemy import text
from .. import get_conn

# ---------- helpers ----------
def _json(status: int, payload: dict):
    return jsonify(payload), status

def _unauth(msg="unauthorized"):
    return _json(401, {"error": msg})

def _forbid(msg="forbidden"):
    return _json(403, {"error": msg})

def _not_found():
    return _json(404, {"error": "not_found"})

def _decode_jwt_from_auth_header() -> Optional[dict]:
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    token = auth.split(None, 1)[1]
    try:
        return jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
    except Exception:
        return None

# ---------- top-level auth ----------
def require_auth(roles: Optional[Iterable[str]] = None):
    """Require a valid JWT; optional role filter."""
    roles = set(roles or [])
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            payload = _decode_jwt_from_auth_header()
            if not payload:
                return _unauth()
            g.user_id  = int(payload.get("sub") or 0)
            g.user_email = payload.get("email")
            g.user_role  = payload.get("role")
            if not g.user_id:
                return _unauth()
            if roles and g.user_role not in roles:
                return _forbid("insufficient_role")
            return fn(*args, **kwargs)
        return wrapper
    return deco

def require_admin(fn):
    return require_auth(roles={"Admin"})(fn)

# ---------- project-level RBAC ----------
def _fetch_user_project_level(conn, user_id: int, project_id: int) -> str | None:
    row = conn.execute(
        text("""
            SELECT
              CASE
                -- treat owners as editors for access purposes
                WHEN p.owner_user_id = :uid THEN 'edit'
                WHEN pa.access_level IS NOT NULL THEN pa.access_level
                ELSE NULL
              END AS level
            FROM projects p
            LEFT JOIN project_access pa
              ON pa.project_id = p.id AND pa.user_id = :uid
            WHERE p.id = :pid
        """),
        {"uid": user_id, "pid": project_id},
    ).mappings().one_or_none()
    return row["level"] if row else None

def require_project_access(access: str):
    """
    access: 'view' or 'edit'
    owner has full rights; 'edit' implies view.
    """
    assert access in {"view", "edit"}
    def deco(fn):
        @wraps(fn)
        def wrapper(project_id, *args, **kwargs):
            if getattr(g, "user_id", None) is None:
                return _unauth()
            with get_conn() as conn:
                lvl = _fetch_user_project_level(conn, int(g.user_id), int(project_id))
                if lvl is None:
                    # distinguish no-project vs no-access
                    exists = conn.execute(text("SELECT 1 FROM projects WHERE id=:pid"), {"pid": project_id}).scalar()
                    return (_not_found() if not exists else _forbid())
                if access == "view" and lvl in {"owner", "edit", "view"}:
                    return fn(project_id, *args, **kwargs)
                if access == "edit" and lvl in {"owner", "edit"}:
                    return fn(project_id, *args, **kwargs)
                return _forbid()
        return wrapper
    return deco

# ---------- self-or-admin utility ----------
def require_self_or_admin(param_name: str = "user_id"):
    """For routes like /users/<user_id>/..."""
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if getattr(g, "user_id", None) is None:
                return _unauth()
            target = int(kwargs.get(param_name))
            if g.user_role == "Admin" or g.user_id == target:
                return fn(*args, **kwargs)
            return _forbid()
        return wrapper
    return deco
