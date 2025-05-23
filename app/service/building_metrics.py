import json

with open ('data/building_metrics.json', 'r') as f:
    bm_data = json.load(f)
class BuildingMetrics:
    def __init__(self):
        self.metrics = {}

    def read_metrics(self, bm_data):
        self.metrics = bm_data

    def get_metric_value(self, name):
        return self.metrics.get(name, {}).get("value")
