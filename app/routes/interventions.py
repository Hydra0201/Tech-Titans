# app/routes/interventions.py
from __future__ import annotations
from flask import Blueprint, request, jsonify, current_app, g
from sqlalchemy import text
from .. import get_conn
from ..services.rules_intervention import intervention_recompute
import jwt  # <-- added

interventions_bp = Blueprint("interventions", __name__)

# --- minimal inline JWT helpers -------------------------------------------
def _get_bearer_token():
    auth = request.headers.get("Authorization", "")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    return auth.split(None, 1)[1]

def _decode_jwt(token: str):
    if not token:
        return None
    secret = current_app.config.get("JWT_SECRET")
    if not secret:
        return None
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
# ---------------------------------------------------------------------------

# --- helpers ---------------------------------------------------------------

def _parse_bool(v: str | None) -> bool:
    return bool(v) and v.strip().lower() in {"1", "true", "t", "yes", "y", "on"}

def _project_exists(conn, project_id: int) -> bool:
    return conn.execute(text("SELECT 1 FROM projects WHERE id = :pid"), {"pid": project_id}).scalar_one_or_none() is not None

def _intervention_exists(conn, intervention_id: int) -> bool:
    return conn.execute(text("SELECT 1 FROM interventions WHERE id = :iid"), {"iid": intervention_id}).scalar_one_or_none() is not None

# --- routes ----------------------------------------------------------------

@interventions_bp.get("/hello")
def get_health():
    """Lightweight DB connectivity check."""
    conn = get_conn()
    row = conn.execute(text("SELECT 1 AS ok")).one()
    return {"ok": row.ok}, 200

@interventions_bp.post("/projects/<int:project_id>/apply")
def apply_intervention(project_id: int):
    """
    Body: { "intervention_id": <int> }
    Query: ?dry_run=1 to preview without saving

    Applies all dependency rules where this intervention is the cause and
    upserts new runtime scores for affected interventions.
    """
    # JWT required (no role/ownership change to behavior)
    token = _get_bearer_token()
    payload = _decode_jwt(token)
    if not payload:
        return {"error": "unauthorized"}, 401
    # Expose if you ever need it later; 
    g.user_id = payload.get("sub")
    g.user_role = payload.get("role")
    g.user_email = payload.get("email")

    data = request.get_json(silent=True) or {}
    try:
        cause_id = int(data.get("intervention_id"))
    except Exception:
        return {"error": "bad_request", "message": "intervention_id (int) is required"}, 400

    dry_run = _parse_bool(request.args.get("dry_run"))
    conn = get_conn()

    # Pre-checks
    if not _project_exists(conn, project_id):
        return {"error": "not_found", "message": "project not found"}, 404
    if not _intervention_exists(conn, cause_id):
        return {"error": "not_found", "message": "intervention not found"}, 404

    tx = conn.begin()
    try:
        # (kept) first recompute call
        new_scores = intervention_recompute(conn, project_id, cause_id)

        inserted = 0
        if not dry_run:
            # Records that an intervention has been implemented
            res = conn.execute(
                text("""
                    INSERT INTO implemented_interventions (project_id, impl_id)
                    VALUES (:pid, :iid)
                    ON CONFLICT (project_id, impl_id) DO NOTHING
                    RETURNING 1
                """),
                {"pid": project_id, "iid": cause_id},
            )
            inserted = res.rowcount or 0

        # (kept) second recompute call exactly as in your current logic
        new_scores = intervention_recompute(conn, project_id, cause_id)

        if dry_run:
            tx.rollback()
        else:
            tx.commit()

        return jsonify({
            "project_id": project_id,
            "cause_intervention_id": cause_id,
            "updated": len(new_scores),
            "new_scores": {int(k): float(v) for k, v in new_scores.items()},
            "dry_run": dry_run,
            "implemented_row_inserted": bool(inserted),
        }), 200
    except Exception:
        if tx.is_active:
            tx.rollback()
        current_app.logger.exception("apply_intervention failed")
        return {"error": "server_error"}, 500
