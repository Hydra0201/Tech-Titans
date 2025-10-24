# app/__init__.py
import os
from flask import Flask, g
from dotenv import load_dotenv
from sqlalchemy import create_engine
from flask_cors import CORS
from flask import current_app

def create_app():
    load_dotenv()
    app = Flask(__name__)

    # ---- Config ----
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL is not set. Put it in your .env")
    app.config["PG_ENGINE"] = create_engine(dsn, pool_pre_ping=True)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Auth config (used by /auth/login)
    app.config["JWT_SECRET"] = os.environ.get("JWT_SECRET", "dev-secret-change-me")
    app.config["JWT_EXPIRES_HOURS"] = int(os.environ.get("JWT_EXPIRES_HOURS", "24"))

    # ---- Per-request connection management ----
    @app.teardown_appcontext
    def _close_request_conn(exc):
        conn = g.pop("_pg_conn", None)
        if conn is not None:
            conn.close()

    # ---- Blueprints ----
    from app.routes.projects import projects_bp
    from app.routes.theme_weights import theme_weights_bp
    from app.routes.interventions import interventions_bp
    from app.routes.building_metrics import metrics_bp
    from app.routes.auth import auth_bp
    from app.routes.admin_users import admin_users_bp
    from app.routes.data_ingestion import ingestion_bp
    from app.routes.report import report_bp
    from app.routes.graph import graphs_bp

    app.register_blueprint(projects_bp, url_prefix="/api")        
    app.register_blueprint(theme_weights_bp, url_prefix="/api")
    app.register_blueprint(interventions_bp, url_prefix="/api")
    app.register_blueprint(metrics_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(admin_users_bp, url_prefix="/api")
    app.register_blueprint(ingestion_bp, url_prefix="/api")
    app.register_blueprint(report_bp, url_prefix="/api")
    app.register_blueprint(graphs_bp)

    return app


def get_conn():
    engine = current_app.config["PG_ENGINE"]
    conn = engine.connect()
    
    if conn.in_transaction():
        conn.rollback()
        
    return conn