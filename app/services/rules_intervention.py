from sqlalchemy import text
from sqlalchemy.engine import Connection
from .types import InterventionRule
from typing import List

def fetch_intervention_rules(conn: Connection) -> List[InterventionRule]:
    """
    Load intervention dependency rules from DB, return as list of InterventionRule dataclasses.
    """
    rows = conn.execute(
        text(
            """
            SELECT
                id,
                cause_intervention,
                effected_intervention,
                metric_type,
                lower_bound AS lower,
                upper_bound AS upper,
                multiplier,
                reasoning
            FROM intervention_effects
            """
        )
    ).mappings().all()

    out: List[InterventionRule] = []
    for r in rows:
        out.append(InterventionRule(
            id=int(r["id"]),
            cause_intervention_id=int(r["cause_intervention"]),
            effect_intervention_id=int(r["effected_intervention"]),
            metric_type=str(r["metric_type"]),
            lower=(float(r["lower"]) if r["lower"] is not None else None),
            upper=(float(r["upper"]) if r["upper"] is not None else None),
            multiplier=float(r["multiplier"]),
            reason=str(r["reasoning"]),
        ))
    return out    
