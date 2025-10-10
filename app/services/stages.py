
from typing import Any, List, Mapping
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy import text
from typing import List, Mapping, Any

def recommendations(conn: Connection, project_id: int, limit: int = 3) -> List[Mapping[str, Any]]:
    """
    Return top-N eligible recommendations for a project, filtered by stage rules (mutex/prereq).
    Each row has: intervention_id, name, adjusted_base_effectiveness.
    """
    rows = conn.execute(
        text("""
            SELECT r.intervention_id, i.name, r.adjusted_base_effectiveness
            FROM runtime_scores r
            JOIN interventions i ON i.id = r.intervention_id
            WHERE r.project_id = :pid
              AND NOT EXISTS (
                SELECT 1 FROM implemented_interventions ii
                WHERE ii.project_id = :pid
                  AND ii.impl_id = r.intervention_id
              )
              AND (
                    COALESCE(i.is_stage, FALSE) = FALSE
                    OR (
                      NOT EXISTS (
                        SELECT 1 FROM stages s
                        WHERE s.src_intervention_id = r.intervention_id
                          AND s.relation_type = 'prereq'
                          AND NOT EXISTS (
                            SELECT 1 FROM implemented_interventions ii
                            WHERE ii.impl_id = s.dst_intervention_id
                              AND ii.project_id = :pid
                          )
                      )
                      AND
                      NOT EXISTS (
                        SELECT 1 FROM stages s
                        WHERE s.src_intervention_id = r.intervention_id
                          AND s.relation_type = 'mutex'
                          AND EXISTS (
                            SELECT 1 FROM implemented_interventions ii
                            WHERE ii.impl_id = s.dst_intervention_id
                              AND ii.project_id = :pid
                          )
                      )
                    )
                )
            ORDER BY r.adjusted_base_effectiveness DESC
            LIMIT :lim
        """),
        {"pid": project_id, "lim": limit},
    ).mappings().all()
    return rows

# This implementation requires:
    # an "is_stage" flag in the interventions table
    # an implemented_interventions table containing FK to intervention id ()
    # and a stages table with a src_intervention_id, dst_intervention_id, and relation_type