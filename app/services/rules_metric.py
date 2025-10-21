from typing import Dict, List
from sqlalchemy import text
from sqlalchemy.engine import Connection
from .types import MetricRule, in_bounds


def fetch_metric_rules(conn: Connection) -> List[MetricRule]:
    """
    Load metric rules from DB, return as list of MetricRule dataclasses.
    """
    rows = conn.execute(
        text(
            """
            SELECT
              id,
              cause AS metric_name,
              effected_intervention AS intervention_id,
              lower_bound AS lower,
              upper_bound AS upper,
              multiplier,
              reasoning
            FROM metric_effects
            """
        )
    ).mappings().all()

    out: List[MetricRule] = []
    for r in rows:
        out.append(MetricRule(
            id=int(r["id"]),
            metric_name=str(r["metric_name"]),
            intervention_id=int(r["intervention_id"]),
            lower=(float(r["lower"]) if r["lower"] is not None else None),
            upper=(float(r["upper"]) if r["upper"] is not None else None),
            multiplier=float(r["multiplier"]),
            reason=r["reasoning"],
        ))
    return out


def save_project_metrics(conn: Connection, project_id: int, metrics: Dict[str, float]) -> int:
    ALLOWED = {
        "levels",
        "external_wall_area",
        "footprint_area",
        "opening_pct",
        "wall_to_floor_ratio",
        "footprint_gifa",
        "gifa_total",
        "external_openings_area",
        "avg_height_per_level",
    }

    # Filter + coerce types
    updates: Dict[str, float] = {}
    for name, val in (metrics or {}).items():
        if name in ALLOWED and val is not None:
            try:
                updates[name] = float(val)
            except Exception:
                pass

    if not updates:
        return 0

    # Create row if does not exist
    conn.execute(
        text("""
            INSERT INTO projects (id, name, status, created_at, updated_at)
            VALUES (:project_id, 'Untitled', 'draft', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO NOTHING
        """),
        {"project_id": project_id},
    )

    set_clause = ", ".join(f"{col} = :{col}" for col in updates.keys())
    params = {**updates, "project_id": project_id}

    # Insert values
    res = conn.execute(
        text(f"""
            UPDATE projects
               SET {set_clause},
                   updated_at = CURRENT_TIMESTAMP
             WHERE id = :project_id
        """),
        params,
    )
    return int(res.rowcount or 0)

def metric_recompute(conn: Connection, project_id: int) -> Dict[int, float]:
    """
    Recompute runtime scores based on metric rules.
    Returns: {intervention_id: adjusted_base_effectiveness}
    """

    base_rows = conn.execute(
        text("""
            SELECT id, COALESCE(base_effectiveness, 0) AS base_effectiveness
            FROM interventions
        """)
    ).mappings().all()
    base_eff = {int(r["id"]): float(r["base_effectiveness"]) for r in base_rows}
    if not base_eff:
        return {}

    rules = fetch_metric_rules(conn)
    if not rules:
        return base_eff 

    needed_cols = sorted({r.metric_name for r in rules})

    select_list = ", ".join(f'"{c}"' for c in needed_cols)
    proj_row = conn.execute(
        text(f"""
            SELECT {select_list}
            FROM projects
            WHERE id = :pid
        """),
        {"pid": project_id},
    ).mappings().one_or_none()

    metrics_by_name: Dict[str, float] = {}
    if proj_row:
        for c in needed_cols:
            v = proj_row.get(c)
            if v is not None:
                metrics_by_name[c] = float(v)

    mult_by_intervention: Dict[int, float] = {iid: 1.0 for iid in base_eff}

    for rule in rules:
        mv = metrics_by_name.get(rule.metric_name)
        if in_bounds(mv, rule.lower, rule.upper):
            mult_by_intervention[rule.intervention_id] *= rule.multiplier

    return {iid: base_eff[iid] * mult_by_intervention[iid] for iid in base_eff}



def upsert_runtime_scores(conn: Connection, project_id: int, scores: Dict[int, float]) -> None:
    """For a given project_id, updates adjusted_base_effectiveness values with contents of the scores Dict"""
    if not scores:
        return

    payload = [
        {"project_id": project_id, "intervention_id": int(iid), "score": float(score)}
        for iid, score in scores.items()
    ]

    conn.execute(
        text("""
            INSERT INTO runtime_scores (project_id, intervention_id, adjusted_base_effectiveness)
            VALUES (:project_id, :intervention_id, :score)
            ON CONFLICT (project_id, intervention_id)
            DO UPDATE SET adjusted_base_effectiveness = EXCLUDED.adjusted_base_effectiveness
        """),
        payload,
    )