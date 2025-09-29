# app/routes/building_metrics.py
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import text
from .. import get_conn
from ..services import rules_metric

metrics_bp = Blueprint("metrics", __name__)

@metrics_bp.get("/hello")  # DB health
def get_health():
    conn = get_conn()
    row = conn.execute(text("SELECT 1 AS ok")).one()
    return {"ok": row.ok}, 200


# ---------- Metrics ingest + recompute ----------
@metrics_bp.post("/projects/<int:project_id>/metrics")
def send_metrics(project_id: int):
    payload = request.get_json(silent=True) or {}

    def parse_bool(s: str | None) -> bool:
        return (s or "").strip().lower() in {"1", "true", "t", "yes", "y", "on"}

    dry_run = parse_bool(request.args.get("dry_run"))

    # ACCEPT BOTH SHAPES: {metrics:{...}} OR RAW {...}
    metrics_raw = payload.get("metrics") if "metrics" in payload else payload
    if not isinstance(metrics_raw, dict) or not metrics_raw:
        return {"error": "bad_request", "message": "missing metrics"}, 400

    try:
        metrics = {str(k): float(v) for k, v in metrics_raw.items() if v is not None}
    except Exception:
        return {
            "error": "bad_request",
            "message": "metrics values must be numbers"
        }, 400

    conn = get_conn()
    # safe if a transaction is already active (e.g., in tests)
    tx = conn.begin() if not conn.in_transaction() else conn.begin_nested()
    try:
        # write metrics -> recompute -> upsert scores
        rules_metric.save_project_metrics(conn, project_id, metrics)
        scores = rules_metric.metric_recompute(conn, project_id)
        rules_metric.upsert_runtime_scores(conn, project_id, scores)

        if dry_run:
            tx.rollback()
        else:
            tx.commit()

        # tiny debug signal in logs (remove if noisy)
        try:
            base_count = conn.execute(text("SELECT COUNT(*) FROM interventions")).scalar_one()
            rule_count = conn.execute(text("SELECT COUNT(*) FROM metric_effects")).scalar_one()
            current_app.logger.info("metrics recompute: interventions=%s rules=%s updated=%s",
                                    base_count, rule_count, len(scores))
        except Exception:
            pass

        return {"project_id": project_id, "updated": len(scores), "dry_run": dry_run}, 200
    except Exception:
        if tx.is_active:
            tx.rollback()
        current_app.logger.exception("Metrics recompute failed")
        return {"error": "Metrics recompute failed"}, 500


# ---------- Top 3 recommendations ----------
@metrics_bp.get("/projects/<int:project_id>/recommendations")
def get_recommendations(project_id: int):
    conn = get_conn()
    rows = conn.execute(
        text("""
            SELECT r.intervention_id, i.name, r.adjusted_base_effectiveness
            FROM runtime_scores AS r
            JOIN interventions AS i ON i.id = r.intervention_id
            WHERE r.project_id = :pid
            ORDER BY r.adjusted_base_effectiveness DESC
            LIMIT 3
        """),
        {"pid": project_id},
    ).mappings().all()
    return {"recommendations": [dict(r) for r in rows]}, 200


# ---------- List a user's projects ----------
def _fetch_user_projects(conn, user_id: int):
    return conn.execute(
        text("""
            SELECT COALESCE(json_agg(p), '[]'::json) AS data
            FROM (
              SELECT id, name, status, project_type, building_type, location,
                     levels, external_wall_area, footprint_area, opening_pct,
                     wall_to_floor_ratio, footprint_gifa, gifa_total,
                     external_openings_area, avg_height_per_level,
                     created_at, updated_at
              FROM projects
              WHERE owner_user_id = :user_id
              ORDER BY updated_at DESC
            ) p
        """),
        {"user_id": user_id},
    ).scalar_one()

@metrics_bp.get("/users/<int:user_id>/projects")
def list_user_projects(user_id: int):
    conn = get_conn()
    data = _fetch_user_projects(conn, user_id)
    return {"projects": data}, 200

# Optional compatibility alias
@metrics_bp.get("/projects/user/<int:user_id>")
def list_user_projects_compat(user_id: int):
    conn = get_conn()
    data = _fetch_user_projects(conn, user_id)
    return {"projects": data}, 200
