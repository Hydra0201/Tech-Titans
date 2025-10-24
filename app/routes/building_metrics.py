# app/routes/building_metrics.py
from flask import Blueprint, request, jsonify, current_app, g
from sqlalchemy import text
from .. import get_conn
from ..services import rules_metric, stages
from ..services.weightings import apply_weights
import jwt

metrics_bp = Blueprint("metrics", __name__)

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

@metrics_bp.post("/projects/<int:project_id>/metrics")
def send_metrics(project_id: int):
    # JWT required
    token = _get_bearer_token()
    payload = _decode_jwt(token)
    if not payload:
        return {"error": "unauthorized"}, 401

    # Optional: expose on g for future RBAC
    g.user_id = payload.get("sub")
    g.user_role = payload.get("role")
    g.user_email = payload.get("email")

    payload_json = request.get_json(silent=True) or {}

    def parse_bool(s: str | None) -> bool:
        return (s or "").strip().lower() in {"1", "true", "t", "yes", "y", "on"}

    dry_run = parse_bool(request.args.get("dry_run"))

    # Accept both shapes: {metrics:{...}} or raw {...}
    metrics_raw = payload_json.get("metrics") if "metrics" in payload_json else payload_json
    if not isinstance(metrics_raw, dict) or not metrics_raw:
        return {"error": "bad_request", "message": "missing metrics"}, 400

    try:
        metrics = {str(k): float(v) for k, v in metrics_raw.items() if v is not None}
    except Exception:
        return {"error": "bad_request", "message": "metrics values must be numbers"}, 400

    # Always close the connection (context manager)
    with get_conn() as conn:
        # Safe if caller already opened a transaction (e.g., tests)
        tx = conn.begin() if not conn.in_transaction() else conn.begin_nested()
        try:
            # write metrics -> recompute -> upsert scores -> apply weights
            rules_metric.save_project_metrics(conn, project_id, metrics)
            scores = rules_metric.metric_recompute(conn, project_id)
            rules_metric.upsert_runtime_scores(conn, project_id, scores)

            # Keep theme_weighted_effectiveness in sync
            apply_weights(project_id, conn)

            if dry_run:
                tx.rollback()
            else:
                tx.commit()

            # Tiny debug signal in logs
            try:
                base_count = conn.execute(text("SELECT COUNT(*) FROM interventions")).scalar_one()
                rule_count = conn.execute(text("SELECT COUNT(*) FROM metric_effects")).scalar_one()
                current_app.logger.info(
                    "metrics recompute: interventions=%s rules=%s updated=%s",
                    base_count, rule_count, len(scores)
                )
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
    token = _get_bearer_token()
    payload = _decode_jwt(token)
    if not payload:
        return {"error": "unauthorized"}, 401
    g.user_id = payload.get("sub")
    g.user_role = payload.get("role")
    g.user_email = payload.get("email")

    with get_conn() as conn:
        try:
            rows = stages.recommendations(conn, project_id, limit=3)
            return jsonify({"recommendations": [dict(r) for r in rows]}), 200
        except Exception:
            current_app.logger.exception("failed to get recommendations")
            return {"failed to get recommendations"}, 500

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
    token = _get_bearer_token()
    payload = _decode_jwt(token)
    if not payload:
        return {"error": "unauthorized"}, 401
    g.user_id = payload.get("sub")
    g.user_role = payload.get("role")

    try:
        jwt_uid = int(str(g.user_id))
    except Exception:
        return {"error": "unauthorized"}, 401
    if (jwt_uid != int(user_id)) and (g.user_role != "Admin"):
        return {"error": "forbidden"}, 403

    with get_conn() as conn:
        data = _fetch_user_projects(conn, user_id)
        return {"projects": data}, 200

# Optional compatibility alias
@metrics_bp.get("/projects/user/<int:user_id>")
def list_user_projects_compat(user_id: int):
    token = _get_bearer_token()
    payload = _decode_jwt(token)
    if not payload:
        return {"error": "unauthorized"}, 401
    g.user_id = payload.get("sub")
    g.user_role = payload.get("role")

    try:
        jwt_uid = int(str(g.user_id))
    except Exception:
        return {"error": "unauthorized"}, 401
    if (jwt_uid != int(user_id)) and (g.user_role != "Admin"):
        return {"error": "forbidden"}, 403

    with get_conn() as conn:
        data = _fetch_user_projects(conn, user_id)
        return {"projects": data}, 200
