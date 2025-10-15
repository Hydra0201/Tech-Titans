from flask import Blueprint, jsonify, current_app
from .. import get_conn
from ..services import report as report_service

report_bp = Blueprint("report", __name__)

@report_bp.get("/projects/<int:project_id>/implemented")
def get_implemented(project_id: int):
    try:
        with get_conn() as conn:
            implemented = report_service.implemented(conn, project_id)
        return jsonify({
            "project_id": project_id,
            "implemented_interventions": implemented
        }), 200
    except Exception as e:
        current_app.logger.exception("Failed to generate implemented interventions")
        return jsonify({"error": "failed to generate implemented intervention output"}), 500


