from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.engine import Connection

def implemented(conn: Connection, project_id: int) -> List[Dict[str, Any]]:
    """
    Return implemented interventions for a project, ordered by score (desc).
    Each item has: intervention_id:int, name:str, score:float|None
    """
    result = conn.execute(text("""
        SELECT
          ii.impl_id AS intervention_id,
          i.name,
          rs.theme_weighted_effectiveness AS score
        FROM implemented_interventions AS ii
        JOIN interventions AS i
          ON i.id = ii.impl_id
        LEFT JOIN runtime_scores AS rs
          ON rs.project_id = ii.project_id
         AND rs.intervention_id = ii.impl_id
        WHERE ii.project_id = :project_id
        ORDER BY COALESCE(rs.theme_weighted_effectiveness, 0) DESC, i.name
    """), {"project_id": project_id})
    return [dict(m) for m in result.mappings().all()]
