# app/routes/projects.py
from __future__ import annotations
from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy import text
from .. import get_conn

projects_bp = Blueprint("projects", __name__)

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
                # ignore bad cast; let DB stay unchanged on PATCH or omit on POST
                pass
    return out

def _row_to_dict(row) -> dict:
    d = dict(row)
    # json-safe datetimes & decimals
    if isinstance(d.get("created_at"), datetime):
        d["created_at"] = d["created_at"].isoformat()
    if isinstance(d.get("updated_at"), datetime):
        d["updated_at"] = d["updated_at"].isoformat()

    # Cast Numeric -> float for known numeric fields
    for k in _NUM_FIELDS:
        if d.get(k) is not None:
            d[k] = float(d[k])
    return d

# --- routes --------------------------------------------------

@projects_bp.post("/projects")
def create_project():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name") or "").strip()
    if not name:
        return {"error": "bad_request", "message": "name is required"}, 400

    # coerce optional fields
    fields = _coerce_payload(data)
    fields["name"] = name

    # build insert
    cols = ", ".join(fields.keys())
    params = {k: fields[k] for k in fields}
    vals = ", ".join(f":{k}" for k in fields)

    sql = f"""
        INSERT INTO projects ({cols})
        VALUES ({vals})
        RETURNING
          id, name, status, project_type, building_type, location,
          levels, external_wall_area, footprint_area, opening_pct,
          wall_to_floor_ratio, footprint_gifa, gifa_total,
          external_openings_area, avg_height_per_level,
          created_at, updated_at
    """

    conn = get_conn()
    tx = conn.begin()
    try:
        row = conn.execute(text(sql), params).mappings().one()
        tx.commit()
        return jsonify({"project": _row_to_dict(row)}), 201
    except Exception:
        if tx.is_active: tx.rollback()
        return {"error": "server_error"}, 500


@projects_bp.get("/projects/<int:project_id>")
def get_project(project_id: int):
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
    data = request.get_json(silent=True) or {}
    updates = _coerce_payload(data)

    # keep only allowed fields
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
