import os

from flask import Flask

def create_app():
    app = Flask(__name__)

    from app.routes.interventions import interventions_bp
    from app.routes.building_metrics import metrics_bp
    from app.routes.scaling import scaling_bp

    app.register_blueprint(interventions_bp, url_prefix='/api')
    app.register_blueprint(metrics_bp, url_prefix='/api')
    app.register_blueprint(scaling_bp, url_prefix='/api')

    return app



