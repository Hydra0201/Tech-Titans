from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.engine import Connection

def implemented(conn: Connection, project_id: int) -> List[Dict[str, Any]]:
    result = conn.execute(text("""
        SELECT intervention_id, theme_weighted_effectiveness AS score
        FROM runtime_scores
        WHERE project_id = :project_id
        ORDER BY score DESC
    """), {"project_id": project_id})
    return [dict(r._mapping) for r in result]