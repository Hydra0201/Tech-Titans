# app/routes/interventions.py
from __future__ import annotations
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import text
from .. import get_conn
from ..services.rules_intervention import intervention_recompute

interventions_bp = Blueprint("interventions", __name__)

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
        }), 200
    except Exception:
        if tx.is_active:
            tx.rollback()
        current_app.logger.exception("apply_intervention failed")
        return {"error": "server_error"}, 500
