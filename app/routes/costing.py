# app/routes/costing.py
from flask import Blueprint, request, current_app
from .. import get_conn
from ..services import costing
import jwt  # <-- added

costs = Blueprint("costs", __name__)

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


@costs.get("/projects/<int:project_id>/costs")
def get_costs(project_id: int):
    """
    GET /projects/{project_id}/costs - return cost token estimate.

    Auth: Bearer JWT required.

    Description:
      Computes the project's current cost level as an integer number of cost tokens

    Responses:
      - 200: {"project_id": <int>, "cost_tokens": <int>}
      - 401: {"error":"unauthorized"}
      - 500: {"error":"failed to calc cost tokens"}
    """
    token = _get_bearer_token()
    payload = _decode_jwt(token)
    if not payload:
        return {"error": "unauthorized"}, 401

    try:
        with get_conn() as conn:
            tokens: int = costing.calc_cost_level(conn, project_id)
        return {"project_id": project_id, "cost_tokens": tokens}, 200
    except Exception:
        return {"error": "failed to calc cost tokens"}, 500
