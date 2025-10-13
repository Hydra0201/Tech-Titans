# app/routes/data_ingestion.py
from pathlib import Path
from flask import Blueprint, jsonify, request, current_app, g
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection
from ..services.data_ingestion import actions, sql_stmts
from app import get_conn
import jwt  # <-- added

ingestion_bp = Blueprint("ingest", __name__)

BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = "app/data_ingestion/interventions.xlsx"
actions.EXCEL_PATH = EXCEL_PATH

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


@ingestion_bp.post("/ingest")
def ingest():
    # JWT + Admin required
    token = _get_bearer_token()
    payload = _decode_jwt(token)
    if not payload:
        return jsonify({"error": "unauthorized"}), 401
    if payload.get("role") != "Admin":
        return jsonify({"error": "forbidden"}), 403
    g.user_id = payload.get("sub")

    results = {}

    resp, status = actions.read_sheet(
        sheet="themes",
        columns=["id", "name"],
        stmt=sql_stmts.themes,
    )
    results["themes"] = resp
    if status != 200:
        return jsonify(results), status

    resp, status = actions.read_sheet(
        sheet="interventions",
        columns=["id", "name", "theme_id", "base_effectiveness"],
        stmt=sql_stmts.interventions,
    )
    results["interventions"] = resp
    if status != 200:
        return jsonify(results), status

    resp, status = actions.read_sheet(
        sheet="stages",
        columns=["src_intervention_id", "dst_intervention_id", "relation_type"],
        stmt=sql_stmts.stages,
    )
    results["stages"] = resp
    if status != 200:
        return jsonify(results), status

    resp, status = actions.read_sheet(
        sheet="metric_effects",
        columns=["id", "cause", "effected_intervention", "metric_type", "lower_bound", "upper_bound", "multiplier"],
        stmt=sql_stmts.metric_effects,
    )
    results["metric_effects"] = resp
    if status != 200:
        return jsonify(results), status

    resp, status = actions.read_sheet(
        sheet="intervention_effects",
        columns=["id", "cause_intervention", "effected_intervention", "metric_type", "lower_bound", "upper_bound", "multiplier"],
        stmt=sql_stmts.intervention_effects,
    )
    results["intervention_effects"] = resp
    if status != 200:
        return jsonify(results), status

    return jsonify({"ok": True, "details": results}), 200


@ingestion_bp.delete("/clear_db")
def clear():
    # JWT + Admin required
    token = _get_bearer_token()
    payload = _decode_jwt(token)
    if not payload:
        return jsonify({"error": "unauthorized"}), 401
    if payload.get("role") != "Admin":
        return jsonify({"error": "forbidden"}), 403
    g.user_id = payload.get("sub")

    try:
        actions.clear_db()
        return jsonify({"ok": True}), 200
    except Exception:
        return jsonify({"error": "failed_to_clear"}), 500
