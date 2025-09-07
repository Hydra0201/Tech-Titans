import math
from flask import Blueprint, request, current_app
from sqlalchemy import text
from .. import get_conn
from ..services.rules_intervention import intervention_recompute
from ..services.weightings import normalise_weights, apply_weights
from flask import jsonify

interventions_bp = Blueprint('interventions', __name__)

@interventions_bp.route('/hello', methods=['GET']) # DB Test
def get_health():
    conn = get_conn()
    row = conn.execute(text("SELECT 1 AS ok")).one()
    return {"ok": row.ok}, 200


@interventions_bp.route('health', methods=['GET'])
def health():
    return jsonify(ok=True)

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
    

@interventions_bp.route('/projects/<int:project_id>/weightings', methods=['POST'])
def apply_weightings(project_id: int):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict) or not payload:
        return {"error": "Expected JSON object of {theme_id: weighting}."}, 400
    
    try:
        weightings = {
            int(k): float(v)
            for k, v in payload.items()
            if math.isfinite(float(v)) and float(v) >= 0.0
        }
    except (ValueError, TypeError) as e:
        return {"error": f"Invalid mapping (ids must be ints, weights numeric >= 0): {e}"}, 400

    if not weightings:
        return {"error": "No valid (non-negative, finite) weights provided."}, 400

    conn = get_conn()
    try:
        normalise_weights(project_id, weightings, conn)
        updated = apply_weights(project_id, conn)
    except Exception as e:
        return {"error": f"Failed to apply weightings: {e}"}, 500

    return jsonify({
        "project_id": project_id,
        "themes_received": len(weightings),
        "rows_updated": updated
    }), 200
