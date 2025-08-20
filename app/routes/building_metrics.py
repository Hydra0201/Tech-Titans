from flask import Blueprint, request, jsonify, current_app
from ..services import scoring
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import text
from .. import get_conn

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route('/hello', methods=['GET']) # DB Test
def get_health():
    conn = get_conn()
    row = conn.execute(text("SELECT 1 AS ok")).one()
    return {"ok": row.ok}, 200

# Route to POST project building metrics to DB
@metrics_bp.route('/projects/<int:project_id>/metrics', methods=['POST'])
def send_metrics(project_id):
    payload = request.get_json(force=True)

    if not payload:
        return jsonify({"message": "Error: Form data does not match expected format."}), 400 
    
    try:
        metrics = {int(k): float(v) for k, v in payload["metrics"].items()} # Type check
    except Exception:
        return jsonify({"error": "Metrics must be numeric mapping: {metric_id: number}"}), 400

    conn = get_conn()

    try:
        with conn.begin():
            scoring.save_project_metrics(conn, project_id, {int(k): float(v) for k,v in metrics.items()})
            scores = scoring.metric_recompute(conn, project_id)
            scoring.upsert_runtime_scores(conn, project_id, scores)
        return {"updated": len(scores)}, 200
    except Exception as e:
        current_app.logger.exception("Metrics recompute failed")
        return {"error": "Metrics recompute failed"}, 500


# Fetch top three interventions from DB
@metrics_bp.get("/projects/<int:project_id>/recommendations")
def get_recommendations(project_id: int):

    conn = get_conn()
    rows = conn.execute(
        text(
            """
            SELECT r.intervention_id, i.name, r.adjusted_base_effectiveness
            FROM runtime_scores AS r
            JOIN interventions AS i ON i.id = r.intervention_id
            WHERE r.project_id = :pid
            ORDER BY r.adjusted_base_effectiveness DESC
            LIMIT 3
            """
        ),
        {"pid": project_id},
    ).mappings().all()
    return jsonify({"recommendations": rows}), 200
