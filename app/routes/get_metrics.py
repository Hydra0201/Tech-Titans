from flask import Blueprint
from service.building_metrics import BuildingMetrics
import json

with open("data/building_metrics.json", "r") as f:
    bm_data = json.load(f)
metrics = BuildingMetrics()

get_metrics_bp = Blueprint('get_metrics', __name__)

@get_metrics_bp.route('get_metrics')
def get_metrics():
    metrics.read_metrics(bm_data)
    return "Metrics successfully read"