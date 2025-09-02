from flask import Blueprint, send_from_directory
from pathlib import Path

docs_bp = Blueprint("docs_bp", __name__)

APP_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = APP_ROOT / "docs"

@docs_bp.route("/openapi.json", methods=["GET"])
def openapi_json():
    return send_from_directory(DOCS_DIR, "openapi.json", mimetype="application/json")

@docs_bp.route("/docs", methods=["GET"])
def swagger_ui():
    return """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>API Docs</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist/swagger-ui.css"/>
  </head>
  <body>
    <div id="swagger"></div>
    <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
    <script>
      // from /api/docs this fetches /api/openapi.json
      window.ui = SwaggerUIBundle({ url: 'openapi.json', dom_id: '#swagger' });
    </script>
  </body>
</html>
"""

