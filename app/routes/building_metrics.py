from flask import Blueprint, request, jsonify, current_app
from ..services import scoring
from sqlalchemy import text
from .. import get_conn

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route('/hello', methods=['GET']) # DB Test
def get_health():
    conn = get_conn()
    row = conn.execute(text("SELECT 1 AS ok")).one()
    return {"ok": row.ok}, 200


# Route to POST project building metrics to DB
@metrics_bp.post("/projects/<int:project_id>/metrics")
def send_metrics(project_id: int):
    payload = request.get_json(silent=True) or {}

    # Dealing with Python string coercion bs
    def parse_bool(s: str | None) -> bool:
        if s is None: 
            return False
        return s.strip().lower() in {"1","true","t","yes","y","on"}

    dry_run = parse_bool(request.args.get("dry_run"))

    metrics_raw = payload.get("metrics")
    if not isinstance(metrics_raw, dict):
        return {"error": "Invalid payload: missing 'metrics' dict"}, 400

    try:
        metrics = {str(k): float(v) for k, v in (metrics_raw or {}).items()}
    except Exception:
        return {"error": "Metrics must be numeric mapping: {metric_name: number}"}, 400

    conn = get_conn()                  
    tx = conn.begin()                   
    try:
        scoring.save_project_metrics(conn, project_id, metrics)
        scores = scoring.metric_recompute(conn, project_id)
        scoring.upsert_runtime_scores(conn, project_id, scores)

        if dry_run:
            tx.rollback()               # rollback chnges (test run)
        else:
            tx.commit()                 # persist changes

        return {"updated": len(scores), "dry_run": dry_run}, 200
    except Exception:
        tx.rollback()
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

# Fetch existing projects
@metrics_bp.get("/projects/<int:user_id>")
def get_projects(user_id: int):

    conn = get_conn()
    rows = conn.execute(
    text("""
        SELECT COALESCE(json_agg(p), '[]'::json) AS data
        FROM (
        SELECT id, name, status, project_type, building_type, levels,
                external_wall_area, footprint_area, opening_pct, wall_to_floor_ratio,
                footprint_gifa, gifa_total, external_openings_area, avg_height_per_level,
                created_at, updated_at
        FROM projects
        WHERE owner_user_id = :user_id
        ORDER BY updated_at DESC
        ) p
    """),
    {"user_id": user_id},
    ).scalar_one()
    return {"projects": rows}, 200