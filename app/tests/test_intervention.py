import pytest
from service.intervention import Intervention, Stage



def test_intervention_base_effect_only():
    intervention = Intervention(name="Test A", theme="Construction activity emissions", base_effect=0.5)
    assert len(intervention.stages) == 1
    assert intervention.stages[0].name == "Standalone"
    assert intervention.stages[0].base_effect == 0.5

def test_intervention_stages_only():
    stages = [Stage("Design", 0.3), Stage("Build", 0.5)]
    intervention = Intervention(name="Test B", theme="Low waste design strategy", stages=stages)
    assert intervention.stages == stages

def test_intervention_both():
    stages = [Stage("Foo", 0.1)]
    with pytest.raises(ValueError):
        Intervention(name="Invalid", theme="Enhanced Construction Monitoring", stages=stages, base_effect=0.5)

def test_intervention_neither():
    with pytest.raises(ValueError):
        Intervention(name="Invalid", theme="Structural Optimisation")

