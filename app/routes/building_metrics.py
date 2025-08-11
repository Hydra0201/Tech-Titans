from flask import Blueprint, request, jsonify, current_app
from services import scoring
import psycopg2
from psycopg2.extras import RealDictCursor
# import DB

metrics_bp = Blueprint('metrics', __name__)

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

    conn: psycopg2.Connection = current_app.config["PG_CONN"]
    try:
        with conn:
            scoring.save_project_metrics(conn, project_id, metrics)
            scores = scoring.metric_recompute(conn, project_id)
            scoring.upsert_runtime_scores(conn, project_id, scores)
        return jsonify({"Updated": len(scores)}), 200
    except Exception as e:
        return jsonify({"Error": "Metrics recompute failed"}), 500


# Fetch top three interventions from DB
@metrics_bp.route("/projects/<int:project_id>/recommendations", methods=["GET"])
def get_recommendations(project_id):
    conn: psycopg2.Connection = current_app.config["PG_CONN"]   
    with conn.cursor(cursor_factory=RealDictCursor) as cur: # RealDictCursor is psycopg2, need to change this to row factor if we change versions
        cur.execute("""
            SELECT r.intervention_id, i.name, r.score
            FROM runtime_scores r
            JOIN interventions i ON i.id = r.intervention_id
            WHERE r.project_id = %s
            ORDER BY r.score DESC
            LIMIT 3
        """, (project_id,))
        return jsonify({"recommendations": cur.fetchall()}), 200