from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
import psycopg2 # Just 'psycopg' is the newer library, should perhaps migrate

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

def fetch_metric_rules(conn) -> List[MetricRule]:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
              intervention_id,
              metric_id,
              lower_bound AS lower,
              upper_bound AS upper,
              multiplier,
              reason
            FROM metric_rules
        """)
        colnames = [desc[0] for desc in cur.description]
        rows = [dict(zip(colnames, row)) for row in cur.fetchall()]
    return [MetricRule(**row) for row in rows]


def save_project_metrics(conn, project_id: int, metrics: Dict[int, float]) -> None:
    # metrics: {metric_id: value}
    with conn.cursor() as cur:
        for mid, val in metrics.items():
            cur.execute("""
                INSERT INTO project_metrics (project_id, metric_id, value)
                VALUES (%s, %s, %s)
                ON CONFLICT (project_id, metric_id)
                DO UPDATE SET value = EXCLUDED.value
            """, (project_id, mid, float(val)))

def metric_recompute(conn, project_id: int) -> dict[int, float]:
    with conn.cursor() as cur:
        cur.execute("SELECT id, base_effectiveness FROM interventions")
        base_eff = {iid: float(base) for iid, base in cur.fetchall()}

    # project metrics (id -> value)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT metric_id, value
            FROM project_metrics
            WHERE project_id = %s
        """, (project_id,))
        metrics = {mid: float(val) for mid, val in cur.fetchall()}

    metric_rules = fetch_metric_rules(conn)

    # Seed multipliers with 1.0
    mult_by_intervention: dict[int, float] = {intervention_id: 1.0 for intervention_id in base_eff}

    def in_bounds(metric_value, low, high):
        if metric_value is None: return False
        if low is not None and metric_value < low: return False
        if high is not None and metric_value > high: return False
        return True


    # Check each metric rule, add multiplier mult_by_intervention where rule applies
    for rule in metric_rules:
        metric_value = metrics.get(rule.metric_id)
        if in_bounds(metric_value, rule.lower, rule.upper):
            mult_by_intervention[rule.intervention_id] *= rule.multiplier

    return {intervention_id: base_eff[intervention_id] * mult_by_intervention[intervention_id] for intervention_id in base_eff}


# Update / insert into runtime table
def upsert_runtime_scores(conn, project_id: int, scores: Dict[int, float]) -> None:
    with conn.cursor() as cur:
        for intervention_id, score in scores.items():
            cur.execute("""
                INSERT INTO runtime_scores (project_id, intervention_id, score)
                VALUES (%s, %s, %s)
                ON CONFLICT (project_id, intervention_id)
                DO UPDATE SET score = EXCLUDED.score
            """, (project_id, intervention_id, float(score)))