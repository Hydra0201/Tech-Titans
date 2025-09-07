from sqlalchemy import text
from sqlalchemy.engine import Connection
from .types import InterventionRule
from typing import List, Dict

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



from typing import Dict, List
from sqlalchemy import text
from sqlalchemy.engine import Connection

def intervention_recompute(
    conn: Connection,
    project_id: int,
    cause_id: int,
) -> Dict[int, float]:
    """
    Apply all unconditional intervention_effects where cause_intervention = :cause_id.
    Multiplies current runtime scores for affected interventions and upserts them.
    Returns {effect_intervention_id: new_score}.
    """

    rules = conn.execute(text("""
        SELECT
          id,
          effected_intervention AS effect_id,
          multiplier
        FROM intervention_effects
        WHERE cause_intervention = :cid
    """), {"cid": cause_id}).mappings().all()

    if not rules:
        return {}

    mult_by_effect: Dict[int, float] = {}
    for r in rules:
        effect_id = int(r["effect_id"])
        m = float(r["multiplier"]) 
        mult_by_effect[effect_id] = mult_by_effect.get(effect_id, 1.0) * m

    if not mult_by_effect:
        return {}

    # Read runtime scores, fallback to base_effectiveness if runtime score missing
    effect_ids = sorted(mult_by_effect.keys())
    rows = conn.execute(text("""
        SELECT i.id AS intervention_id,
               COALESCE(rs.adjusted_base_effectiveness, COALESCE(i.base_effectiveness,0)) AS current_score
        FROM interventions i
        LEFT JOIN runtime_scores rs
          ON rs.intervention_id = i.id AND rs.project_id = :pid
        WHERE i.id = ANY(:ids)
    """), {"pid": project_id, "ids": effect_ids}).mappings().all()

    payload: List[Dict[str, float]] = []
    new_scores: Dict[int, float] = {}
    for row in rows:
        iid = int(row["intervention_id"])
        new_val = float(row["current_score"]) * mult_by_effect[iid]
        new_scores[iid] = new_val
        payload.append({"project_id": project_id, "intervention_id": iid, "score": new_val})

    conn.execute(text("""
        INSERT INTO runtime_scores (project_id, intervention_id, adjusted_base_effectiveness)
        VALUES (:project_id, :intervention_id, :score)
        ON CONFLICT (project_id, intervention_id)
        DO UPDATE SET adjusted_base_effectiveness = EXCLUDED.adjusted_base_effectiveness
    """), payload)

    return new_scores