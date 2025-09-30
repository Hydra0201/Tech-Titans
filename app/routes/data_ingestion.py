from pathlib import Path
from flask import Blueprint
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection

from app import get_conn


ingestion = Blueprint("costs", __name__)

BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = BASE_DIR / "interventions.xlsx" 
SHEET_NAME = "interventions"

@ingestion.post("/ingest")
def ingest():
    try:
        with get_conn() as conn:
            df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
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

            conn.execute(stmt, records)
            conn.commit()
        return ({"success": "updated DB" }), 200
    except Exception:
        return({"error": "failed to update DB"}), 500