import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection

def load_interventions_excel(conn: Connection, path="inter.xlsx", sheet="interventions") -> int:

    df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.where(pd.notnull(df), None)

    records = df[["id", "name", "theme_id", "base_effectiveness"]].to_dict("records")

    if not records:
        return 0

    stmt = text("""
        INSERT INTO interventions (id, name, theme_id, base_effectiveness)
        VALUES (:id, :name, :theme_id, :base_effectiveness)
        ON CONFLICT (id) DO UPDATE
        SET name = EXCLUDED.name,
            theme_id = EXCLUDED.theme_id,
            base_effectiveness = EXCLUDED.base_effectiveness
    """)

    with conn.begin():
        conn.execute(stmt, records)

    return len(records)
