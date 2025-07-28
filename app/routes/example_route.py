from flask import Blueprint

example_bp = Blueprint('bp_name', __name__)

@example_bp.route('hi')
def hi():
    return "hi"