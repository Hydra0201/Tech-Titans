from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.engine import Connection

def implemented(conn: Connection, project_id: int) -> List[Dict[str, Any]]:
    result = conn.execute(text("""
        SELECT
          rs.intervention_id,
          i.name,
          rs.theme_weighted_effectiveness AS score
        FROM runtime_scores rs
        LEFT JOIN interventions i
          ON i.id = rs.intervention_id
        WHERE rs.project_id = :project_id
        ORDER BY score DESC
    """), {"project_id": project_id})
    return [dict(r._mapping) for r in result]
