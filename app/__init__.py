import os

from flask import Flask

def create_app():
    app = Flask(__name__)

    from app.routes.example_route import example_bp
    app.register_blueprint(example_bp, url_prefix='/api')

    return app



