from flask import Blueprint, request, current_app
from sqlalchemy import text
from .. import get_conn
from ..services.rules_intervention import intervention_recompute

interventions_bp = Blueprint('interventions', __name__)

@interventions_bp.route('/hello', methods=['GET']) # DB Test
def get_health():
    conn = get_conn()
    row = conn.execute(text("SELECT 1 AS ok")).one()
    return {"ok": row.ok}, 200



@interventions_bp.route('/projects/<int:project_id>/apply', methods=['POST'])
def apply_intervention(project_id: int):
    payload = request.get_json(silent=True) or {}
    try:
        cause_id = int(payload["intervention_id"])
    except Exception:
        return {"error": "intervention_id (int) is required"}, 400

    dry_run = (request.args.get("dry_run","").lower() in {"1","true","yes","on"})
    conn = get_conn()
    tx = conn.begin()
    try:
        out = intervention_recompute(conn, project_id, cause_id)
        tx.rollback() if dry_run else tx.commit()
        return {"updated": len(out), "new_scores": out, "dry_run": dry_run}, 200
    except Exception:
        tx.rollback()
        current_app.logger.exception("apply_one failed")
        return {"error": "apply_one failed"}, 500