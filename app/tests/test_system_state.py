import json
import pytest
from service import system_state
from service.intervention import Intervention



@pytest.fixture
def be_data():
    with open('data/base_effectiveness.json', 'r') as f:
        return json.load(f)

@pytest.fixture
def dep_data():
    with open('data/intervention_dependencies.json', 'r') as f:
        return json.load(f)



# Tests score calculation of hardcoded intervention instance
def test_theme_score_calc(be_data, dep_data): 
    intervention = Intervention(name="Test A", theme="Indoor Air Quality", base_effect=0.5)

    ss = system_state.SystemState()
    ss.initialise_themes(be_data)
    ss.apply_intervention(intervention, dep_data)

    assert "Test A" in ss.implemented_interventions

    expected_modifier = sum(
        d["effect_percentage"] / 100.0 
        for d in dep_data 
        if d["source_intervention"] == "Test A" and d["target_theme"] == "Indoor Air Quality"
    )
    expected_score = 0.5 * (1 + expected_modifier)

    assert ss.theme_scores[intervention.theme] == pytest.approx(expected_score)
