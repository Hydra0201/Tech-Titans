import os

from flask import Flask, g
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def create_app():
    load_dotenv()

    app = Flask(__name__)


    dsn = os.environ["DATABASE_URL"]
    engine = create_engine(
        dsn,
        pool_pre_ping=True,
    )

    app.config["PG_ENGINE"] = engine

    @app.teardown_appcontext
    def _close_request_conn(exc):
        conn = g.pop("_pg_conn", None)
        if conn is not None:
            conn.close()

    from app.routes.interventions import interventions_bp
    from app.routes.building_metrics import metrics_bp
    from app.routes.scaling import scaling_bp
    from app.routes.auth import auth_bp
    from app.routes.admin_users import admin_users_bp

    app.register_blueprint(interventions_bp, url_prefix='/api')
    app.register_blueprint(metrics_bp, url_prefix='/api')
    app.register_blueprint(scaling_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(admin_users_bp, url_prefix="/api")

    return app


def get_conn():
    """One connection per request; pooled under the hood."""
    from flask import current_app
    if "_pg_conn" not in g:
        g._pg_conn = current_app.config["PG_ENGINE"].connect()
    return g._pg_conn


