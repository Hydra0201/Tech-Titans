import pytest
import json
from service.intervention import Intervention
from service.system_state import SystemState
from service.recommender import Recommender
from service.building_metrics import BuildingMetrics

# Tests core app logic across Intervention, SystemState, Recommender and BuildingMetrics

@pytest.fixture
def be_data():
    with open('data/base_effectiveness.json', 'r') as f:
        return json.load(f)

@pytest.fixture
def metrics_data():
    with open('data/building_metrics.json', 'r') as f:
        return json.load(f)


def test_full(be_data, metrics_data):

    target_scores = {
        "Reducing Operational Carbon": 1.5,
        "Reducing Embodied Carbon": 1.0
    }


    metrics = BuildingMetrics()
    metrics.read_metrics(metrics_data)

    interventions = [
        Intervention("Low carbon concrete", "Reducing Embodied Carbon", base_effect=0.3),
        Intervention("External Wall U-Value enhancements", "Reducing Operational Carbon", base_effect=0.2)
    ]
    for i in interventions:
        i.apply_metrics(metrics)

    state = SystemState()
    state.update_target_scores(target_scores)
    state.initialise_themes(be_data)
    state.target_scores = {
        "Reducing Operational Carbon": 1.5,
        "Embodied Carbon": 1.0
    }

    recommender = Recommender(state, interventions)
    

    recs = recommender.recommend("Reducing Operational Carbon")

    assert len(recs) == 1
    assert recs[0].name == "External Wall U-Value enhancements"
