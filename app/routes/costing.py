# app/routes/building_metrics.py
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import text
from .. import get_conn
from ..services import costing


costs = Blueprint("costs", __name__)

@costs.get("/projects/<int:project_id>/costs")
def send_costs(project_id: int):
    try:
        with get_conn() as conn:
            tokens: int = costing.calc_cost_level(conn, project_id)
        return({"project_id": project_id, "cost_tokens": tokens}), 200
    except Exception:
        return({"error": "failed to calc cost tokens"}), 500


