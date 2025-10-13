# app/routes/theme_weights.py
from __future__ import annotations
from flask import Blueprint, request, jsonify, current_app, g
from sqlalchemy import text
from ..services.weightings import apply_weights
from .. import get_conn
import jwt  # <-- added

theme_weights_bp = Blueprint("theme_weights", __name__, url_prefix="/api")

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
# --------------------------------------------------------------------------

# --- helpers ---------------------------------------------------------------

def _parse_bool(v: str | None) -> bool:
    if not v:
        return False
    return v.strip().lower() in {"1", "true", "t", "yes", "y", "on"}

def _require_editor_access(conn, project_id: int) -> bool:
    """
    Hook for RBAC. Currently no-op unless AUTH_ENFORCED=True.
    Later:
      - decode JWT
      - check project_access for (user_id, project_id) access_level == 'editor'
    """
    if not current_app.config.get("AUTH_ENFORCED", False):
        return True
    # TODO: implement real check with JWT + project_access
    return True

# --- routes ---------------------------------------------------------------

@theme_weights_bp.get("/themes")
def list_themes():
    # JWT required
    token = _get_bearer_token()
    if not _decode_jwt(token):
        return {"error": "unauthorized"}, 401

    conn = get_conn()
    rows = conn.execute(
        text("SELECT id, name, description FROM themes ORDER BY id ASC")
    ).mappings().all()
    return jsonify({"themes": [dict(r) for r in rows]}), 200


@theme_weights_bp.get("/projects/<int:project_id>/themes")
@theme_weights_bp.get("/projects/<int:project_id>/theme-scores")  # alias for convenience/tests
def get_project_theme_weightings(project_id: int):
    # JWT required
    token = _get_bearer_token()
    payload = _decode_jwt(token)
    if not payload:
        return {"error": "unauthorized"}, 401
    g.user_id = payload.get("sub")
    g.user_role = payload.get("role")

    """
    Return ALL themes with any saved scores for this project (LEFT JOIN).
    weight_raw/weight_norm are null if not saved.
    """
    conn = get_conn()

    # Optional: 404 if project doesn't exist
    proj = conn.execute(
        text("SELECT 1 FROM projects WHERE id = :pid"),
        {"pid": project_id},
    ).scalar_one_or_none()
    if proj is None:
        return {"error": "not_found", "message": "project not found"}, 404

    rows = conn.execute(
        text("""
            SELECT
                t.id   AS id,
                t.name AS name,
                pts.weight_raw,
                pts.weight_norm
            FROM themes AS t
            LEFT JOIN project_theme_weightings AS pts
              ON pts.theme_id = t.id AND pts.project_id = :pid
            ORDER BY t.id
        """),
        {"pid": project_id},
    ).mappings().all()

    items = [
        {
            "id": r["id"],
            "name": r["name"],
            "weight_raw": float(r["weight_raw"]) if r["weight_raw"] is not None else None,
            "weight_norm": float(r["weight_norm"]) if r["weight_norm"] is not None else None,
        }
        for r in rows
    ]

    return jsonify({
        "project_id": project_id,
        "themes": items,   # UI uses this
        "weights": items,  # compatibility / convenience
    }), 200


# Accept both PUT (preferred) and POST (compat) for a full save
@theme_weights_bp.put("/projects/<int:project_id>/theme-scores")
@theme_weights_bp.post("/projects/<int:project_id>/themes")
def upsert_project_theme_weightings(project_id: int):
    # JWT required
    token = _get_bearer_token()
    payload = _decode_jwt(token)
    if not payload:
        return {"error": "unauthorized"}, 401
    g.user_id = payload.get("sub")
    g.user_role = payload.get("role")

    """
    Full-save sliders for a project.
    Body: { "weights": { "<theme_id>": number, ... }, "dry_run"?: bool }
    """
    payload_json = request.get_json(silent=True) or {}
    weights_raw = payload_json.get("weights")

    if not isinstance(weights_raw, dict) or not weights_raw:
        return {"error": "bad_request", "message": "missing 'weights' mapping"}, 400

    # normalize & validate -> {int(theme_id): float(weight)}
    parsed: dict[int, float] = {}
    try:
        for k, v in weights_raw.items():
            tid = int(k)
            val = float(v)
            if val < 0:
                return {"error": "bad_request", "message": "weights must be >= 0"}, 400
            parsed[tid] = val
    except Exception:
        return {"error": "bad_request", "message": "weights must be mapping of {theme_id: number}"}, 400

    total = sum(parsed.values())
    normalized = {tid: (0.0 if total <= 0 else (val / total)) for tid, val in parsed.items()}
    dry_run = _parse_bool(request.args.get("dry_run")) or bool(payload_json.get("dry_run"))

    conn = get_conn()
    tx = conn.begin()
    try:
        # (Optional) ensure project exists
        exists = conn.execute(text("SELECT 1 FROM projects WHERE id = :pid"), {"pid": project_id}).scalar_one_or_none()
        if exists is None:
            tx.rollback()
            return {"error": "not_found", "message": "project not found"}, 404

        # Upsert weights
        for tid, raw in parsed.items():
            conn.execute(text("""
                INSERT INTO project_theme_weightings (project_id, theme_id, weight_raw, weight_norm)
                VALUES (:pid, :tid, :raw, :norm)
                ON CONFLICT (project_id, theme_id)
                DO UPDATE SET weight_raw = EXCLUDED.weight_raw,
                              weight_norm = EXCLUDED.weight_norm
            """), {"pid": project_id, "tid": tid, "raw": raw, "norm": normalized[tid]})

        if dry_run:
            tx.rollback()
            updated_scores = 0
        else:
            tx.commit()
            # Apply weights so theme_weighted_effectiveness is fresh
            updated_scores = apply_weights(project_id, conn)

        return jsonify({
            "project_id": project_id,
            "dry_run": dry_run,
            "updated": len(parsed),
            "sum_raw": float(total),
            "sum_norm": float(sum(normalized.values())),
            "normalized": {tid: float(v) for tid, v in normalized.items()},
            "scores_weighted_updated": int(updated_scores),
        }), 200

    except Exception:
        if tx.is_active:
            tx.rollback()
        current_app.logger.exception("theme weight upsert failed")
        return {"error": "server_error"}, 500
