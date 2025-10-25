from pathlib import Path
from flask import Blueprint, jsonify, request, current_app, g
from ..services.data_ingestion import actions
import traceback
import jwt 

ingestion_bp = Blueprint("ingest", __name__)

BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = "app/data_ingestion/interventions.xlsx"
actions.EXCEL_PATH = EXCEL_PATH

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

@ingestion_bp.post("/ingest")
def ingest():
    """
    POST /ingest - upsert reference data from Excel (Admin only).

    Auth: Bearer JWT with role=Admin.

    Description:
      Reads the configured Excel workbook (themes, interventions, stages,
      metric_effects, intervention_effects) and upserts records by *name*.

    Request: (no body) - uses server-side EXCEL_PATH.

    Responses:
      - 200: {"ok": true, "details": { "themes": {...}, "interventions": {...},
                                       "stages": {...}, "metric_effects": {...},
                                       "intervention_effects": {...} }}
      - 401: {"error":"unauthorized"}
      - 403: {"error":"forbidden"}
      - 500: {"error": "...", "trace": "...", "details": {...}}
    """

    token = _get_bearer_token()
    payload = _decode_jwt(token)
    if not payload:
        return jsonify({"error": "unauthorized"}), 401
    if payload.get("role") != "Admin":
        return jsonify({"error": "forbidden"}), 403
    g.user_id = payload.get("sub")

    results = {}
    try:
        resp, status = actions.upsert_themes_by_name()
        results["themes"] = resp
        if status != 200: return jsonify(results), status

        resp, status = actions.upsert_interventions_by_name()
        results["interventions"] = resp
        if status != 200: return jsonify(results), status

        resp, status = actions.upsert_stages_by_names()
        results["stages"] = resp
        if status != 200: return jsonify(results), status

        resp, status = actions.upsert_effects_by_names(
            sheet="metric_effects",
            id_key_cause="cause",
            id_key_effect="effected_intervention",
        )
        results["metric_effects"] = resp
        if status != 200: return jsonify(results), status

        resp, status = actions.upsert_effects_by_names(
            sheet="intervention_effects",
            id_key_cause="cause_intervention",
            id_key_effect="effected_intervention",
        )
        results["intervention_effects"] = resp
        if status != 200: return jsonify(results), status

        return jsonify({"ok": True, "details": results}), 200

    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc(), "details": results}), 500


@ingestion_bp.delete("/clear_db")
def clear():
    """
    DELETE /clear_db - remove all reference/runtime data (Admin only).

    Auth: Bearer JWT with role=Admin.

    Description:
      Clears themes, interventions, effects, stages, runtime scores, and related tables.

    Responses:
      - 200: {"ok": true}
      - 401: {"error":"unauthorized"}
      - 403: {"error":"forbidden"}
      - 500: {"error":"failed_to_clear"}
    """

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
