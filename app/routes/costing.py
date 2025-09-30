# app/routes/costing.py
from flask import Blueprint, jsonify, request
from .. import get_conn
from ..services import costing

costs = Blueprint("costs", __name__, url_prefix="/api")

@costs.get("/projects/<int:project_id>/costs")
def get_costs(project_id: int):
    try:
        with get_conn() as conn:
            tokens: int = costing.calc_cost_level(conn, project_id)
        return jsonify({"project_id": project_id, "cost_tokens": int(tokens)}), 200
    except Exception:
        return jsonify({"error": "failed_to_calc_cost_tokens"}), 500
