import math
from sqlalchemy import text
from sqlalchemy.engine import Connection


def calc_cost_level(conn: Connection, project_id: int):
    """
    Return how many 'cost tokens' to display = floor(total_cost_weight / step_size).
    If project_id is provided, limit to that set of implemented interventions.
    """
    # Get the size of a token
    step_size = conn.execute(
        text("SELECT step_size FROM config LIMIT 1")
    ).scalar_one()


    # Sum weights
    total_weight = conn.execute(
        text("""
            SELECT COALESCE(SUM(i.cost_weight), 0) AS total_weight
            FROM implemented_interventions AS ii
            JOIN interventions AS i
              ON i.id = ii.impl_id
            WHERE (ii.project_id = :pid)
        """),
        {"pid": project_id}
    ).scalar_one()

    # Convert to token count
    tokens = math.floor(total_weight / step_size) if step_size > 0 else 0
    return tokens



# TODO:
# 1. Table containing a project's currently selected interventions, linked to their project ID

# 2. Just add a cost_weight (float) column to the interventions table

# 3. Somewhere in the DB we need to store a "step_size", which represents the token weight score which makes up a cost token
    # Might be good to make a config table for it in case other variables like this come up, that way its easy for CostPlan to change.
