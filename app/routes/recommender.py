from flask import Blueprint, request, current_app
from sqlalchemy import text
from .. import get_conn
from ..services.rules_intervention import intervention_recompute

docs_bp = Blueprint('docs_bp', __name__)

@docs_bp_bp.route('/hello', methods=['GET']) # DB Test
def openapi_json():
    with open(os.path.join(os.path.dirname(__file__), "openapi.yaml"), "r") as f:
        spec = yaml.safe_load(f)
    return jsonify(spec)

@docs_bp.route("/docs")
def swagger_ui():
    return """
<!doctype html>
<html>
  <head>
    <title>API Docs</title>
    <meta charset="utf-8"/>
    <link rel="stylesheet"
      href="https://unpkg.com/swagger-ui-dist/swagger-ui.css"/>
  </head>
  <body>
    <div id="swagger"></div>
    <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
    <script>
      window.ui = SwaggerUIBundle({ url: '/openapi.json', dom_id: '#swagger' });
    </script>
  </body>
</html>
"""