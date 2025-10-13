from pathlib import Path
from flask import Blueprint, jsonify
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection
from ..services.data_ingestion import actions, sql_stmts
from app import get_conn


ingestion_bp = Blueprint("ingest", __name__)

BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = "app/data_ingestion/interventions.xlsx" 
actions.EXCEL_PATH = EXCEL_PATH


@ingestion_bp.post("/ingest")
def ingest():
    results = {}


    resp, status = actions.read_sheet(
        sheet="themes",
        columns=["id", "name"],
        stmt=sql_stmts.themes,       
    )
    results["themes"] = resp
    if status != 200:
        return jsonify(results), status

    resp, status = actions.read_sheet(
        sheet="interventions",
        columns=["id", "name", "theme_id", "base_effectiveness"],
        stmt=sql_stmts.interventions,
    )
    results["interventions"] = resp
    if status != 200:
        return jsonify(results), status

    resp, status = actions.read_sheet(
        sheet="stages",
        columns=["src_intervention_id", "dst_intervention_id", "relation_type"],
        stmt=sql_stmts.stages,
    )
    results["stages"] = resp
    if status != 200:
        return jsonify(results), status

    resp, status = actions.read_sheet(
        sheet="metric_effects",
        columns=["id", "cause", "effected_intervention", "metric_type", "lower_bound", "upper_bound", "multiplier"],
        stmt=sql_stmts.metric_effects,
    )
    results["metric_effects"] = resp
    if status != 200:
        return jsonify(results), status

    resp, status = actions.read_sheet(
        sheet="intervention_effects",
        columns=["id", "cause_intervention", "effected_intervention", "metric_type", "lower_bound", "upper_bound", "multiplier"],
        stmt=sql_stmts.intervention_effects,
    )
    results["intervention_effects"] = resp
    if status != 200:
        return jsonify(results), status

    return jsonify({"ok": True, "details": results}), 200

@ingestion_bp.delete("/clear_db")
def clear():
    actions.clear_db()