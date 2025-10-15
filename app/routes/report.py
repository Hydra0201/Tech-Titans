from flask import Blueprint, jsonify, current_app, render_template, request, url_for, Response
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


@report_bp.get("/projects/<int:project_id>/report.html")
def report_html(project_id: int):
    with get_conn() as conn:
        implemented = report_service.implemented(conn, project_id)

    graph_url = url_for("graphs.project_graph_svg", project_id=project_id, _external=True)

    return render_template(
        "report.html",
        project_id=project_id,
        implemented=implemented,
        graph_url=graph_url
    )


@report_bp.get("/projects/<int:project_id>/report.pdf")
def report_pdf(project_id: int):

    with get_conn() as conn:
        implemented = report_service.implemented(conn, project_id)

    graph_url = url_for("graphs.project_graph_svg", project_id=project_id, _external=True)

    # Render HTML via Jinja first
    html_str = render_template(
        "report.html",
        project_id=project_id,
        implemented=implemented,
        graph_url=graph_url
    )

    pdf_bytes = HTML(string=html_str, base_url=request.host_url).write_pdf()

    return Response(pdf_bytes, mimetype="application/pdf")
