from pathlib import Path
from typing import Any, Dict, Sequence, Tuple
from flask import Blueprint
import pandas as pd
from sqlalchemy import TextClause, text

from app import get_conn


ingestion = Blueprint("costs", __name__)

BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = BASE_DIR / "interventions.xlsx" 


def clear_db():
    try:
        with get_conn() as conn:
            with conn.begin():

                conn.execute(text("DELETE FROM implemented_interventions"))
                conn.execute(text("DELETE FROM stages"))
                conn.execute(text("DELETE FROM runtime_scores"))
                conn.execute(text("DELETE FROM interventions"))
                conn.execute(text("DELETE FROM themes"))
                conn.execute(text("DELETE FROM intervention_effects"))
                conn.execute(text("DELETE FROM project_theme_weightings"))
        return {"ok": True, "message": "All data cleared"}, 200
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500
    




def read_sheet(sheet: str, columns: Sequence[str], stmt: TextClause) -> tuple[dict[str, Any], int]:
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=sheet, engine="openpyxl")
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.where(pd.notnull(df), None)

        missing = [c for c in columns if c not in df.columns]
        if missing:
            return ({"error": f"missing columns in '{sheet}': {missing}"}, 400)

        records = df[columns].to_dict("records")

        conn = get_conn()        
        with conn.begin():
            if records:
                conn.execute(stmt, records)

        return ({"success": f"{sheet}: processed {len(records)} rows"}, 200)
    except Exception as e:
        return ({"error": f"{sheet}: failed to update DB: {e}"}, 500)