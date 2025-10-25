# app/routes/interventions.py
from __future__ import annotations
from flask import Blueprint, request, jsonify, current_app, g
from sqlalchemy import text
from .. import get_conn
from ..services.rules_intervention import intervention_recompute
from ..services.weightings import apply_weights, decay_by_intervention
import jwt
from typing import List, Dict

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
    return conn.execute(
        text("SELECT 1 FROM projects WHERE id = :pid"),
        {"pid": project_id},
    ).scalar_one_or_none() is not None

def _intervention_exists(conn, intervention_id: int) -> bool:
    return conn.execute(
        text("SELECT 1 FROM interventions WHERE id = :iid"),
        {"iid": intervention_id},
    ).scalar_one_or_none() is not None

# --- routes ----------------------------------------------------------------

@interventions_bp.post("/projects/<int:project_id>/apply")
def apply_intervention(project_id: int):
    """
    POST /projects/{project_id}/apply - apply one intervention.

    Auth: Bearer JWT required.

    Request (JSON):
      - intervention_id (int, required)

    Query:
      - dry_run (bool, optional) - validate/compute without persisting
      - decay (bool, optional) - apply decay after recompute
      - alpha (float, optional, default 0.6) - decay factor
      - floor (float, optional, default 0.0) - lower bound for decay

    Responses:
      - 200: {
          "project_id": int,
          "cause_intervention_id": int,
          "updated": int,
          "new_scores": { "<intervention_id>": <score>, ... },
          "dry_run": bool,
          "insert_attempted": bool,
          "insert_returned_row": bool,
          "verified_persisted": bool,
          "decay_applied": bool,
          "decay_params": {"alpha": float, "floor": float} | null
        }
      - 401: {"error":"unauthorized"}
      - 404: {"error":"not_found", "message": "..."}
      - 500: {"error":"server_error"}
    """
    token = _get_bearer_token()
    payload = _decode_jwt(token)
    if not payload:
        return {"error": "unauthorized"}, 401

    try:
        g.user_id = int(str(payload.get("sub"))) if payload.get("sub") is not None else None
    except Exception:
        g.user_id = None
    g.user_role = payload.get("role")
    g.user_email = payload.get("email")

    data = request.get_json(silent=True) or {}
    try:
        cause_id = int(data.get("intervention_id"))
    except Exception:
        return {"error": "bad_request", "message": "intervention_id (int) is required"}, 400

    dry_run    = _parse_bool(request.args.get("dry_run"))
    want_decay = _parse_bool(request.args.get("decay"))
    try:
        alpha = float(request.args.get("alpha", 0.6))
    except Exception:
        alpha = 0.6
    try:
        floor = float(request.args.get("floor", 0.0))
    except Exception:
        floor = 0.0

    with get_conn() as conn:
        # quick existence checks
        if not _project_exists(conn, project_id):
            return {"error": "not_found", "message": "project not found"}, 404
        if not _intervention_exists(conn, cause_id):
            return {"error": "not_found", "message": "intervention not found"}, 404

        tx = conn.begin() if not conn.in_transaction() else conn.begin_nested()
        try:
            # per-request timeout (doesn't change global DB)
            try:
                conn.exec_driver_sql("SET LOCAL statement_timeout = 8000")
            except Exception:
                pass

            inserted_row = None
            if not dry_run:
                inserted_row = conn.execute(
                    text("""
                        INSERT INTO implemented_interventions (project_id, impl_id, user_id)
                        VALUES (:pid, :iid, :uid)
                        ON CONFLICT (project_id, impl_id) DO NOTHING
                        RETURNING project_id
                    """),
                    {"pid": project_id, "iid": cause_id, "uid": g.user_id},
                ).scalar_one_or_none()

            # recompute / reweight while we still hold the tx
            new_scores = intervention_recompute(conn, project_id, cause_id)
            try:
                apply_weights(project_id, conn)
            except Exception:
                current_app.logger.exception("apply_weights failed (non-fatal)")

            if not dry_run and want_decay:
                try:
                    decay_by_intervention(project_id, cause_id, conn, alpha=alpha, floor=floor)
                except Exception:
                    current_app.logger.exception("decay_by_intervention failed (non-fatal)")

            if dry_run:
                tx.rollback()
            else:
                tx.commit()

        except Exception:
            if tx.is_active:
                tx.rollback()
            current_app.logger.exception("apply_intervention failed")
            return {"error": "server_error"}, 500

    #  verify with a fresh connection that the row actually exists
    verified = False
    if not dry_run:
        with get_conn() as conn2:
            try:
                verified = conn2.execute(
                    text("""
                        SELECT 1 FROM implemented_interventions
                        WHERE project_id = :pid AND impl_id = :iid
                        LIMIT 1
                    """),
                    {"pid": project_id, "iid": cause_id},
                ).scalar_one_or_none() is not None
            except Exception:
                pass

    return jsonify({
        "project_id": project_id,
        "cause_intervention_id": cause_id,
        "updated": len(new_scores),
        "new_scores": {int(k): float(v) for k, v in new_scores.items()},
        "dry_run": dry_run,
        "insert_attempted": not dry_run,
        "insert_returned_row": bool(inserted_row),
        "verified_persisted": bool(verified),
        "decay_applied": (not dry_run and want_decay),
        "decay_params": {"alpha": alpha, "floor": floor} if want_decay else None,
    }), 200
    
    
@interventions_bp.post("/projects/<int:project_id>/apply-batch")
def apply_interventions_batch(project_id: int):
    """
    POST /projects/{project_id}/apply-batch - apply multiple interventions.

    Auth: Bearer JWT required.

    Request (JSON):
      - intervention_ids (list[int], required)

    Query:
      - dry_run (bool, optional) - if true, no inserts/recompute

    Responses:
      - 200: {
          "project_id": int,
          "applied_count": int,
          "intervention_ids": [int, ...],
          "dry_run": bool,
          "next_recommendations": [ { ... up to 3 ... } ],
          "has_more": bool
        }
      - 400: {"error":"bad_request", "message":"..."}
      - 401: {"error":"unauthorized"}
      - 404: {"error":"not_found", "message":"..."}
    """
    token = _get_bearer_token()
    payload = _decode_jwt(token)
    if not payload:
        return {"error": "unauthorized"}, 401
    try:
        g.user_id = int(str(payload.get("sub"))) if payload.get("sub") is not None else None
    except Exception:
        g.user_id = None
    
    # Input validation
    data = request.get_json(silent=True) or {}
    intervention_ids = data.get("intervention_ids", [])
    
    if not isinstance(intervention_ids, list) or not intervention_ids:
        return {"error": "bad_request", "message": "intervention_ids (array) required"}, 400
    
    try:
        intervention_ids = [int(i) for i in intervention_ids]
    except Exception:
        return {"error": "bad_request", "message": "intervention_ids must be integers"}, 400
    
    dry_run = _parse_bool(request.args.get("dry_run"))
    
    with get_conn() as conn:
        # Validate project exists
        if not _project_exists(conn, project_id):
            return {"error": "not_found", "message": "project not found"}, 404
    
        # Validate all interventions exist
        for iid in intervention_ids:
            if not _intervention_exists(conn, iid):
                return {"error": "not_found", "message": f"intervention {iid} not found"}, 404
    
    applied_count = 0
    
    if not dry_run:
        for iid in intervention_ids:
            with get_conn() as conn:
                try:
                    conn.exec_driver_sql("COMMIT")
                    
                    result = conn.execute(
                        text("""
                            INSERT INTO implemented_interventions (project_id, impl_id, user_id)
                            VALUES (:pid, :iid, :uid)
                            ON CONFLICT (project_id, impl_id) DO NOTHING
                            RETURNING project_id, impl_id, user_id
                        """),
                        {"pid": project_id, "iid": iid, "uid": g.user_id},
                    ).fetchone()
                    
                    if result:
                        applied_count += 1
                        conn.exec_driver_sql("COMMIT")
                        
                except Exception as e:
                    current_app.logger.exception(f"Insert failed for intervention {iid}")
        
        # Do recomputes in a separate connection
        if applied_count > 0:
            with get_conn() as compute_conn:
                compute_conn.exec_driver_sql("COMMIT")
                
                for iid in intervention_ids:
                    try:
                        intervention_recompute(compute_conn, project_id, iid)
                    except Exception as e:
                        current_app.logger.exception(f"Recompute failed for intervention {iid}")
                
                # Refresh theme-weighted effectiveness
                try:
                    apply_weights(project_id, compute_conn)
                    compute_conn.exec_driver_sql("COMMIT")
                except Exception:
                    current_app.logger.exception("apply_weights failed (non-fatal)")
    
    # Get fresh recommendations
    with get_conn() as conn2:
        try:
            from ..services.stages import recommendations
            next_recs = recommendations(conn2, project_id, limit=3)
        except Exception:
            current_app.logger.exception("Failed to get next recommendations")
            next_recs = []
    
    return jsonify({
        "project_id": project_id,
        "applied_count": applied_count,
        "intervention_ids": intervention_ids,
        "dry_run": dry_run,
        "next_recommendations": [dict(r) for r in next_recs],
        "has_more": len(next_recs) > 0
    }), 200


@interventions_bp.get("/projects/<int:project_id>/implemented")
def get_implemented_interventions(project_id: int):
    """
    GET /projects/{project_id}/implemented - list implemented interventions.

    Auth: Bearer JWT required.

    Responses:
      - 200: {
          "project_id": int,
          "total_count": int,
          "interventions": [
            {
              "intervention_id": int,
              "name": str,
              "description": str | null,
              "theme_name": str | null,
              "implemented_at": str,          # ISO-8601
              "implemented_by_email": str | null
            }, ...
          ]
        }
      - 401: {"error":"unauthorized"}
      - 404: {"error":"not_found", "message":"project not found"}
    """
    token = _get_bearer_token()
    payload = _decode_jwt(token)
    if not payload:
        return {"error": "unauthorized"}, 401
    
    with get_conn() as conn:
    
        if not _project_exists(conn, project_id):
            return {"error": "not_found", "message": "project not found"}, 404
    
        rows = conn.execute(
            text("""
                SELECT 
                    ii.impl_id as intervention_id,
                    i.name,
                    i.description,
                    t.name as theme_name,
                    ii.implemented_at,  
                    u.email as implemented_by_email
                FROM implemented_interventions ii
                JOIN interventions i ON i.id = ii.impl_id
                LEFT JOIN themes t ON t.id = i.theme_id
                LEFT JOIN users u ON u.id = ii.user_id
                WHERE ii.project_id = :pid
                ORDER BY ii.implemented_at ASC
            """),
            {"pid": project_id}
        ).mappings().all()
    
        return jsonify({
            "project_id": project_id,
            "total_count": len(rows),
            "interventions": [dict(r) for r in rows]
        }), 200
