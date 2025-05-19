import pytest
from service.intervention import Intervention, Stage, InterventionTheme


class DummyTheme(InterventionTheme):
    DESIGN_STRATEGY = "Design Strategy"


def test_intervention_base_effect_only():
    intervention = Intervention(name="Test A", theme=DummyTheme.DESIGN_STRATEGY, base_effect=0.5)
    assert len(intervention.stages) == 1
    assert intervention.stages[0].name == "Standalone"
    assert intervention.stages[0].base_effect == 0.5

def test_intervention_stages_only():
    stages = [Stage("Design", 0.3), Stage("Build", 0.5)]
    intervention = Intervention(name="Test B", theme=DummyTheme.DESIGN_STRATEGY, stages=stages)
    assert intervention.stages == stages

def test_intervention_both():
    stages = [Stage("Foo", 0.1)]
    with pytest.raises(ValueError):
        Intervention(name="Invalid", theme=DummyTheme.DESIGN_STRATEGY, stages=stages, base_effect=0.5)

def test_intervention_neither():
    with pytest.raises(ValueError):
        Intervention(name="Invalid", theme=DummyTheme.DESIGN_STRATEGY)

