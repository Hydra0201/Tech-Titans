from dataclasses import dataclass
from typing import float, List, Optional

@dataclass
class ScoreBreakdown:
    base: float
    metric_factor: float
    dependency_factor: float
    theme_weight: float
    final: float
    reasons: List[str]

@dataclass(frozen=True)
class MetricRule:
    id: int
    metric_name: str
    intervention_id: int
    lower: Optional[float]
    upper: Optional[float]
    multiplier: float
    reason: str

@dataclass(frozen=True)
class InterventionRule:
    id: int
    cause_intervention_id: int
    effect_intervention_id: int
    metric_type: str
    lower: Optional[float]
    upper: Optional[float]
    multiplier: float
    reason: str


def in_bounds(metric_value: Optional[float], low: Optional[float], high: Optional[float]) -> bool:
    if metric_value is None:
        return False
    if low is not None and metric_value < low:
        return False
    if high is not None and metric_value > high:
        return False
    return True