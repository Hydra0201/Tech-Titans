from pathlib import Path
from typing import Any, Iterable, Sequence
from flask import Blueprint
import pandas as pd
from . import sql_stmts
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
                conn.execute(text("DELETE FROM intervention_effects"))
                conn.execute(text("DELETE FROM runtime_scores"))
                conn.execute(text("DELETE FROM interventions"))
                conn.execute(text("DELETE FROM project_theme_weightings"))
                conn.execute(text("DELETE FROM themes"))
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

        if records:
            with get_conn() as conn:
                with conn.begin():
                    conn.execute(stmt, records)

        return ({"success": f"{sheet}: processed {len(records)} rows"}, 200)
    except Exception as e:
        return ({"error": f"{sheet}: failed to update DB: {e}"}, 500)

def upsert_stages_by_names() -> tuple[dict[str, Any], int]:
    """
    Read 'stages' sheet with columns:
      - src_intervention_name
      - dst_intervention_name
      - relation_type
    Map intervention names -> IDs, then upsert into `stages` using:
      (src_intervention_id, dst_intervention_id, relation_type)
    """
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name="stages", engine="openpyxl")
        df = _require(
            df,
            ["src_intervention_name", "dst_intervention_name", "relation_type"],
            "stages",
        )
        recs = df.to_dict("records")

        if not recs:
            return ({"success": "stages: processed 0 rows"}, 200)

        with get_conn() as conn:
            with conn.begin():
                intv_name_to_id = _fetch_name_id_map(conn, "interventions", "name")

                payload = []
                skipped_missing = 0
                skipped_blank_rel = 0

                for r in recs:
                    sname = (r.get("src_intervention_name") or "").strip()
                    dname = (r.get("dst_intervention_name") or "").strip()
                    rtype = (r.get("relation_type") or "").strip()

                    if not rtype:
                        skipped_blank_rel += 1
                        continue
                    if not sname or not dname:
                        skipped_missing += 1
                        continue

                    sid = intv_name_to_id.get(sname.lower())
                    did = intv_name_to_id.get(dname.lower())
                    if sid is None or did is None:
                        skipped_missing += 1
                        continue

                    payload.append({
                        "src_intervention_id": sid,
                        "dst_intervention_id": did,
                        "relation_type": rtype,
                    })

                if payload:
                    conn.execute(sql_stmts.stages, payload)

        msg = f"stages: processed {len(recs)} rows"
        details = []
        if 'skipped_missing' in locals() and skipped_missing:
            details.append(f"skipped {skipped_missing} (missing name/id)")
        if 'skipped_blank_rel' in locals() and skipped_blank_rel:
            details.append(f"skipped {skipped_blank_rel} (blank relation_type)")
        if details:
            msg += " (" + ", ".join(details) + ")"

        return ({"success": msg}, 200)

    except Exception as e:
        return ({"error": f"stages: {e}"}, 500)

def _fetch_name_id_map(conn, table: str, name_col: str = "name") -> dict[str, int]:
    rows = conn.execute(text(f"SELECT id, {name_col} FROM {table}")).mappings().all()
    out = {}
    for r in rows:
        v = r[name_col]
        if v is None:
            continue
        key = str(v).strip().lower()
        if key:
            out[key] = r["id"]
    return out

def _ensure_rows_by_name(conn, table: str, names: Iterable[str]) -> dict[str, int]:
    """
    Ensure each name exists in `table` (expects columns: id IDENTITY, name UNIQUE).
    Returns {name_lower: id}.
    """
    names_clean = [n for n in { (n or "").strip() for n in names } if n]
    if not names_clean:
        return {}

    name_to_id = _fetch_name_id_map(conn, table)
    missing = [n for n in names_clean if n.lower() not in name_to_id]

    if missing:
        conn.execute(text(f"""
            INSERT INTO {table} (name)
            VALUES (:name)
            ON CONFLICT (name) DO NOTHING
        """), [{"name": n} for n in missing])

        name_to_id = _fetch_name_id_map(conn, table)

    return name_to_id

def _require(df, required_cols: list[str], sheet: str):
    df.columns = [c.strip().lower() for c in df.columns]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"missing columns in '{sheet}': {missing}")
    return df.where(pd.notnull(df), None)

def upsert_themes_by_name() -> tuple[dict[str, Any], int]:
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name="themes", engine="openpyxl")
        df = _require(df, ["name"], "themes")
        names = [r["name"] for r in df.to_dict("records") if r["name"]]
        with get_conn() as conn, conn.begin():
            name_to_id = _ensure_rows_by_name(conn, "themes", names)
        return ({"success": f"themes: ensured {len(name_to_id)} rows by name"}, 200)
    except Exception as e:
        return ({"error": f"themes: {e}"}, 500)
    

    
def parse_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    s = str(v).strip().lower()
    return s in {"1", "true", "t", "yes", "y", "on"}


def upsert_interventions_by_name() -> tuple[dict[str, Any], int]:
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name="interventions", engine="openpyxl")
        df = _require(df, ["name", "theme_name", "base_effectiveness", "is_stage"], "interventions")
        recs = df.to_dict("records")

        with get_conn() as conn:
            with conn.begin():
                theme_to_id = _ensure_rows_by_name(conn, "themes", (r["theme_name"] for r in recs))

                payload = []
                skipped_missing_theme = 0

                for r in recs:
                    name  = (r["name"] or "").strip()
                    tname = (r["theme_name"] or "").strip()
                    if not name or not tname:
                        continue

                    tid = theme_to_id.get(tname.lower())
                    if tid is None:
                        skipped_missing_theme += 1
                        continue

                    payload.append({
                        "name":               name,
                        "theme_id":           tid,
                        "base_effectiveness": r["base_effectiveness"],
                        "is_stage":           parse_bool(r.get("is_stage")),
                    })

                if payload:
                    conn.execute(sql_stmts.interventions, payload)

        msg = f"interventions: processed {len(recs)} rows"
        if 'skipped_missing_theme' in locals() and skipped_missing_theme:
            msg += f" (skipped {skipped_missing_theme} missing theme_id)"
        return ({"success": msg}, 200)

    except Exception as e:
        return ({"error": f"interventions: {e}"}, 500)


def _to_float(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except Exception:
        return None
    
LABEL_MAP = {
    # capitalisation
    "strong positive":   "Strong Positive",
    "moderate positive": "Moderate Positive",
    "weak positive":     "Weak Positive",
    "weak negative":     "Weak Negative",
    "moderate negative": "Moderate Negative",
    "strong negative":   "Strong Negative",
    # shorthands
    "sp": "Strong Positive", "mp": "Moderate Positive", "wp": "Weak Positive",
    "wn": "Weak Negative",   "mn": "Moderate Negative", "sn": "Strong Negative",
    "+strong": "Strong Positive", "+moderate": "Moderate Positive", "+weak": "Weak Positive",
    "-weak": "Weak Negative", "-moderate": "Moderate Negative", "-strong": "Strong Negative",
}
    
def normalize_label(v: str | None) -> str | None:
    if not v:
        return None
    key = " ".join(str(v).strip().lower().split())
    return LABEL_MAP.get(key)

def label_to_numeric(v):
    v = normalize_label(v)
    if v == "Strong Positive":   return 1.5
    if v == "Moderate Positive": return 1.3
    if v == "Weak Positive":     return 1.1
    if v == "Weak Negative":     return 0.9
    if v == "Moderate Negative": return 0.7
    if v == "Strong Negative":   return 0.5
    return None

def upsert_effects_by_names(
    *,
    sheet: str,
    id_key_cause: str,
    id_key_effect: str,
) -> tuple[dict[str, Any], int]:
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=sheet, engine="openpyxl")
        if sheet == "metric_effects":
            df = _require(
                df,
                [
                    "cause_name",
                    "effected_intervention_name",
                    "metric_type",
                    "lower_bound",
                    "upper_bound",
                    "multiplier",
                ],
                sheet,
            )
        elif sheet == "intervention_effects":
            df = _require(
                df,
                [
                    "cause_intervention_name",
                    "effected_intervention_name",
                    "metric_type",
                    "lower_bound",
                    "upper_bound",
                    "multiplier",
                ],
                sheet,
            )
        else:
            return ({"error": f"unknown sheet '{sheet}'"}, 400)

        df = df.where(pd.notnull(df), None)
        recs = df.to_dict("records")
        if not recs:
            return ({"success": f"{sheet}: processed 0 rows"}, 200)

        with get_conn() as conn:
            with conn.begin():
                # intervention name to id map
                intv_map = _fetch_name_id_map(conn, "interventions")

                payload = []
                skipped_missing = 0
                skipped_invalid = 0
                for r in recs:
                    metric_type = (r.get("metric_type") or "").strip() or None
                    lb = _to_float(r.get("lower_bound"))
                    ub = _to_float(r.get("upper_bound"))
                    mult = label_to_numeric(r.get("multiplier") or r.get("multiplier_label"))
                    reasoning = (r.get("reasoning") or "").strip() or None


                    if mult is not None and mult <= 0:
                        skipped_invalid += 1
                        continue
                    if lb is not None and ub is not None and not (ub > lb):
                        skipped_invalid += 1
                        continue

                    if sheet == "metric_effects":
                        cause_name = (r.get("cause_name") or "").strip()
                        eff_name   = (r.get("effected_intervention_name") or "").strip()
                        if not cause_name or not eff_name:
                            skipped_missing += 1
                            continue
                        eff_id = intv_map.get(eff_name.lower())
                        if eff_id is None:
                            skipped_missing += 1
                            continue

                        row = {
                            id_key_cause:   cause_name,  
                            id_key_effect:  eff_id,    
                            "metric_type":  metric_type,
                            "lower_bound":  lb,
                            "upper_bound":  ub,
                            "multiplier":   mult,
                            "reasoning":    reasoning,
                        }
                        payload.append(row)

                    else:
                        cause_name = (r.get("cause_intervention_name") or "").strip()
                        eff_name   = (r.get("effected_intervention_name") or "").strip()
                        if not cause_name or not eff_name:
                            skipped_missing += 1
                            continue
                        cause_id = intv_map.get(cause_name.lower())
                        eff_id   = intv_map.get(eff_name.lower())
                        if cause_id is None or eff_id is None:
                            skipped_missing += 1
                            continue

                        row = {
                            id_key_cause:   cause_id,   
                            id_key_effect:  eff_id,   
                            "metric_type":  metric_type,
                            "lower_bound":  lb,
                            "upper_bound":  ub,
                            "multiplier":   mult,
                            "reasoning":    reasoning,
                        }
                        payload.append(row)

                if not payload:
                    msg = f"{sheet}: processed {len(recs)} rows (none inserted)"
                    if skipped_missing:
                        msg += f"; skipped {skipped_missing} missing ID/name"
                    if skipped_invalid:
                        msg += f"; skipped {skipped_invalid} invalid bounds/multiplier"
                    return ({"success": msg}, 200)

 
                seen = set()
                deduped = []
                for p in payload:

                    key = (
                        p[id_key_cause],
                        p[id_key_effect],
                        p.get("metric_type"),
                        p.get("lower_bound"),
                        p.get("upper_bound"),
                        p.get("multiplier"),
                        p.get("reasoning"),
                    )
                    if key in seen:
                        continue
                    seen.add(key)
                    deduped.append(p)

                stmt = (
                    sql_stmts.metric_effects
                    if sheet == "metric_effects"
                    else sql_stmts.intervention_effects
                )
                conn.execute(stmt, deduped)

        msg = f"{sheet}: processed {len(recs)} rows (inserted {len(set(seen))})"
        if skipped_missing:
            msg += f"; skipped {skipped_missing} missing ID/name"
        if skipped_invalid:
            msg += f"; skipped {skipped_invalid} invalid bounds/multiplier"
        return ({"success": msg}, 200)

    except Exception as e:
        return ({"error": f"{sheet}: {e}"}, 500)