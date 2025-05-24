import json

with open ('data/building_metrics.json', 'r') as f:
    bm_data = json.load(f)
class BuildingMetrics:
    def __init__(self):
        self.metrics = {}

    def read_metrics(self, bm_data):
        self.metrics = bm_data["building_metrics"]

    def get_all_metrics(self):
        return self.metrics

    def get_metric_value(self, name):
        return self.metrics.get(name, {}).get("value")
