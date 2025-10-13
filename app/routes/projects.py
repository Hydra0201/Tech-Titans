# app/routes/projects.py
from __future__ import annotations
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, g
import jwt
from sqlalchemy import text
from .. import get_conn
from ..services import rules_metric  # used for optional post-create recompute

projects_bp = Blueprint("projects", __name__)

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

# --- helpers -------------------------------------------------

_NUM_FIELDS = {
    "levels": int,
    "external_wall_area": float,
    "footprint_area": float,
    "opening_pct": float,
    "wall_to_floor_ratio": float,
    "footprint_gifa": float,
    "gifa_total": float,
    "external_openings_area": float,
    "avg_height_per_level": float,
}

_STR_FIELDS = {
    "name", "status", "project_type", "building_type", "location"
}

_ALLOWED_PATCH_FIELDS = set(_NUM_FIELDS.keys()) | _STR_FIELDS

def _coerce_payload(data: dict) -> dict:
    out = {}
    # strings (trim)
    for k in _STR_FIELDS:
        if k in data and data[k] is not None:
            v = str(data[k]).strip()
            out[k] = v if v != "" else None
    # numbers
    for k, caster in _NUM_FIELDS.items():
        if k in data and data[k] is not None:
            try:
                out[k] = caster(data[k])
            except Exception:
                pass
    return out

def _row_to_dict(row) -> dict:
    d = dict(row)
    if isinstance(d.get("created_at"), datetime):
        d["created_at"] = d["created_at"].isoformat()
    if isinstance(d.get("updated_at"), datetime):
        d["updated_at"] = d["updated_at"].isoformat()
    for k in _NUM_FIELDS:
        if d.get(k) is not None:
            d[k] = float(d[k])
    return d

# --- routes --------------------------------------------------
@projects_bp.post("/projects")
def create_project():
    # JWT required; extract owner from token
    token = _get_bearer_token()
    payload = _decode_jwt(token)
    if not payload:
        return {"error": "unauthorized"}, 401
    g.user_id = payload.get("sub")
    g.user_role = payload.get("role")
    try:
        owner_user_id = int(str(g.user_id))
    except Exception:
        return {"error": "unauthorized"}, 401

    data = request.get_json(silent=True) or {}
    name = str(data.get("name") or "").strip()
    if not name:
        return {"error": "bad_request", "message": "name is required"}, 400

    # coerce optional fields
    fields = _coerce_payload(data)
    fields["name"] = name
    fields["owner_user_id"] = owner_user_id  # set owner

    cols = ", ".join(fields.keys())
    vals = ", ".join(f":{k}" for k in fields)
    params = {k: fields[k] for k in fields}

    sql = f"""
        INSERT INTO projects ({cols})
        VALUES ({vals})
        RETURNING
          id, name, status, project_type, building_type, location,
          levels, external_wall_area, footprint_area, opening_pct,
          wall_to_floor_ratio, footprint_gifa, gifa_total,
          external_openings_area, avg_height_per_level,
          owner_user_id, created_at, updated_at
    """

    conn = get_conn()
    tx = conn.begin()
    try:
        row = conn.execute(text(sql), params).mappings().one()
        tx.commit()

        # OPTIONAL: if numeric fields were provided at create-time,
        # run the scoring pipeline immediately so runtime_scores is populated
        project_id = int(row["id"])
        metrics_in_body = {
            k: fields[k] for k in _NUM_FIELDS.keys()
            if k in fields and fields[k] is not None
        }
        if metrics_in_body:
            conn2 = get_conn()
            tx2 = conn2.begin() if not conn2.in_transaction() else conn2.begin_nested()
            try:
                rules_metric.save_project_metrics(conn2, project_id, metrics_in_body)
                scores = rules_metric.metric_recompute(conn2, project_id)
                rules_metric.upsert_runtime_scores(conn2, project_id, scores)
                tx2.commit()
            except Exception:
                if tx2.is_active:
                    tx2.rollback()
                current_app.logger.exception("post-create recompute failed")

        return jsonify({"project": _row_to_dict(row)}), 201
    except Exception:
        if tx.is_active:
            tx.rollback()
        return {"error": "server_error"}, 500


@projects_bp.get("/projects/<int:project_id>")
def get_project(project_id: int):
    # JWT required (no behavior change beyond auth)
    token = _get_bearer_token()
    if not _decode_jwt(token):
        return {"error": "unauthorized"}, 401

    conn = get_conn()
    row = conn.execute(
        text("""
            SELECT id, name, status, project_type, building_type, location,
                   levels, external_wall_area, footprint_area, opening_pct,
                   wall_to_floor_ratio, footprint_gifa, gifa_total,
                   external_openings_area, avg_height_per_level,
                   created_at, updated_at
            FROM projects
            WHERE id = :pid
            LIMIT 1
        """),
        {"pid": project_id},
    ).mappings().one_or_none()

    if not row:
        return {"error": "not_found"}, 404
    return jsonify({"project": _row_to_dict(row)}), 200


@projects_bp.patch("/projects/<int:project_id>")
def patch_project(project_id: int):
    # JWT required
    token = _get_bearer_token()
    if not _decode_jwt(token):
        return {"error": "unauthorized"}, 401

    data = request.get_json(silent=True) or {}
    updates = _coerce_payload(data)
    updates = {k: v for k, v in updates.items() if k in _ALLOWED_PATCH_FIELDS}
    if not updates:
        return {"error": "bad_request", "message": "no valid fields"}, 400

    sets = ", ".join(f"{k} = :{k}" for k in updates.keys())
    updates["pid"] = project_id

    conn = get_conn()
    tx = conn.begin()
    try:
        row = conn.execute(
            text(f"""
                UPDATE projects
                SET {sets}
                WHERE id = :pid
                RETURNING
                  id, name, status, project_type, building_type, location,
                  levels, external_wall_area, footprint_area, opening_pct,
                  wall_to_floor_ratio, footprint_gifa, gifa_total,
                  external_openings_area, avg_height_per_level,
                  created_at, updated_at
            """),
            updates,
        ).mappings().one_or_none()

        if not row:
            tx.rollback()
            return {"error": "not_found"}, 404

        tx.commit()
        return jsonify({"project": _row_to_dict(row)}), 200
    except Exception:
        if tx.is_active: tx.rollback()
        return {"error": "server_error"}, 500


@projects_bp.delete("/projects/<int:project_id>")
def delete_project(project_id: int):
    # JWT required
    token = _get_bearer_token()
    if not _decode_jwt(token):
        return {"error": "unauthorized"}, 401

    conn = get_conn()
    tx = conn.begin()
    try:
        row = conn.execute(
            text("DELETE FROM projects WHERE id = :pid RETURNING id"),
            {"pid": project_id},
        ).mappings().one_or_none()

        if not row:
            tx.rollback()
            return {"error": "not_found"}, 404

        tx.commit()
        return jsonify({"deleted": True, "id": row["id"]}), 200
    except Exception:
        if tx.is_active: tx.rollback()
        return {"error": "server_error"}, 500
