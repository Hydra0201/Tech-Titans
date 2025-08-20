from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from sqlalchemy import text
from sqlalchemy.engine import Connection

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
    intervention_id: int
    metric_id: int
    lower: Optional[float]
    upper: Optional[float]
    multiplier: float
    reason: str

@dataclass(frozen=True)
class DependencyRule:
    cause_intervention_id: int
    effect_intervention_id: int
    lower: Optional[float]
    upper: Optional[float]
    multiplier: float
    reason: str

def fetch_metric_rules(conn: Connection) -> List[MetricRule]:
    """
    Load metric rules from DB, return as list of MetricRule dataclasses.
    """
    rows = conn.execute(
        text(
            """
            SELECT
              intervention_id,
              metric_id,
              lower_bound AS lower,
              upper_bound AS upper,
              multiplier,
              reason
            FROM metric_rules
            """
        )
    ).mappings().all()

    return [MetricRule(**row) for row in rows]



def save_project_metrics(conn: Connection, project_id: int, metrics: Dict[int, float]) -> None:
    """
    Save metrics for a project.
    Expects a table with columns (project_id, metric_id, value)
    and a unique constraint on (project_id, metric_id).
    """
    if not metrics:
        return

    payload = [
        {"project_id": project_id, "metric_id": int(mid), "value": float(val)}
        for mid, val in metrics.items()
    ]

    conn.execute(
        text(
            """
            INSERT INTO projects (project_id, metric_id, value)
            VALUES (:project_id, :metric_id, :value)
            ON CONFLICT (project_id, metric_id)
            DO UPDATE SET value = EXCLUDED.value
            """
        ),
        payload,
    )

def metric_recompute(conn: Connection, project_id: int) -> Dict[int, float]:
    """
    Recompute per-intervention scores for a project based on:
      - interventions.base_effectiveness
      - metric_rules applied to the project’s current metrics
    Returns: {intervention_id: score}
    """
    # Base effectiveness for all interventions
    base_eff = {
        row.id: float(row.base_effectiveness)
        for row in conn.execute(
            text("SELECT id, base_effectiveness FROM interventions")
        ).mappings()
    }

    # Project metrics: metric_id -> value
    metrics = {
        row.metric_id: float(row.value)
        for row in conn.execute(
            text(
                """
                SELECT metric_id, value
                FROM projects
                WHERE project_id = :pid
                """
            ),
            {"pid": project_id},
        ).mappings()
    }

    rules = fetch_metric_rules(conn)

    # Seed multipliers at 1.0
    mult_by_intervention: Dict[int, float] = {iid: 1.0 for iid in base_eff}

    def in_bounds(metric_value: Optional[float], low: Optional[float], high: Optional[float]) -> bool:
        if metric_value is None:
            return False
        if low is not None and metric_value < low:
            return False
        if high is not None and metric_value > high:
            return False
        return True

    # Apply metric rules
    for rule in rules:
        mv = metrics.get(rule.metric_id)
        if in_bounds(mv, rule.lower, rule.upper):
            mult_by_intervention[rule.intervention_id] *= float(rule.multiplier)

    # Final score = base_effectiveness * combined multipliers
    return {
        iid: base_eff[iid] * mult_by_intervention[iid]
        for iid in base_eff
    }




def upsert_runtime_scores(conn: Connection, project_id: int, scores: Dict[int, float]) -> None:
    """
    Upsert computed scores into runtime_scores.
    Expects columns (project_id, intervention_id, score) and unique (project_id, intervention_id).
    """
    if not scores:
        return

    payload = [
        {"project_id": project_id, "intervention_id": int(iid), "score": float(score)}
        for iid, score in scores.items()
    ]

    conn.execute(
        text(
            """
            INSERT INTO runtime_scores (project_id, intervention_id, score)
            VALUES (:project_id, :intervention_id, :score)
            ON CONFLICT (project_id, intervention_id)
            DO UPDATE SET score = EXCLUDED.score
            """
        ),
        payload,
    )