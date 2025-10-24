from sqlalchemy import text
from sqlalchemy.engine import Connection

def _begin_tx(conn: Connection):
    """Open a root tx, or a savepoint if a tx is already active (guards/read SELECTs cause autobegin)."""
    return conn.begin() if not conn.in_transaction() else conn.begin_nested()

def normalise_weights(project_id: int, weightings: dict[int, float], conn: Connection) -> int:
    if not weightings:
        # zero out non-targeted interventions
        with _begin_tx(conn):
            res = conn.execute(
                text("UPDATE runtime_scores SET theme_weighted_effectiveness = 0 WHERE project_id = :pid"),
                {"pid": project_id},
            )
            return int(res.rowcount or 0)

    # Normalise
    clean = {int(k): float(v) for k, v in weightings.items() if float(v) >= 0.0}
    total = sum(clean.values())
    if total <= 0:
        raise ValueError("Sum of weights must be > 0")

    rows = [
        {"pid": project_id, "theme_id": tid, "weight_raw": w, "weight_norm": (w / total)}
        for tid, w in clean.items()
    ]

    with _begin_tx(conn):
        conn.execute(
            text("""
                INSERT INTO project_theme_weightings (project_id, theme_id, weight_raw, weight_norm)
                VALUES (:pid, :theme_id, :weight_raw, :weight_norm)
                ON CONFLICT (project_id, theme_id)
                DO UPDATE SET
                  weight_raw  = EXCLUDED.weight_raw,
                  weight_norm = EXCLUDED.weight_norm
            """),
            rows,
        )
    return len(rows)

def apply_weights(project_id: int, conn: Connection) -> int:
    """theme_weighted_effectiveness = adjusted_base_effectiveness * weight_norm; zero themes with no row."""
    with _begin_tx(conn):
        res = conn.execute(
            text("""
                UPDATE runtime_scores AS r
                SET theme_weighted_effectiveness =
                      COALESCE(r.adjusted_base_effectiveness, 0)
                    * COALESCE(w.weight_norm, 0)
                FROM interventions AS i
                LEFT JOIN project_theme_weightings AS w
                  ON w.project_id = :pid
                 AND w.theme_id   = i.theme_id
                WHERE r.project_id = :pid
                  AND i.id = r.intervention_id
            """),
            {"pid": project_id},
        )
        return int(res.rowcount or 0)

def renormalise_weights(project_id: int, conn: Connection) -> int:
    """Recompute weight_norm from weight_raw"""
    with _begin_tx(conn):
        res = conn.execute(
            text("""
                WITH sumw AS (
                  SELECT COALESCE(SUM(weight_raw), 0) AS s
                  FROM project_theme_weightings
                  WHERE project_id = :pid
                )
                UPDATE project_theme_weightings p
                SET weight_norm = CASE WHEN sumw.s > 0 THEN p.weight_raw / sumw.s ELSE 0 END
                FROM sumw
                WHERE p.project_id = :pid
            """),
            {"pid": project_id},
        )
        return int(res.rowcount or 0)

def decay_by_intervention(project_id: int, intervention_id: int, conn: Connection, alpha=0.6, floor=0.0) -> int:
    """Decay a theme's weighting"""
    sql = """
    WITH target AS (
      SELECT i.theme_id
      FROM interventions i
      WHERE i.id = :iid
    ),
    decayed AS (
      UPDATE project_theme_weightings p
      SET weight_raw = GREATEST(:floor, p.weight_raw * :alpha),
          decay_steps = COALESCE(p.decay_steps, 0) + 1
      FROM target t
      WHERE p.project_id = :pid AND p.theme_id = t.theme_id
      RETURNING 1
    ),
    sumw AS (
      SELECT COALESCE(SUM(weight_raw), 0) AS s
      FROM project_theme_weightings
      WHERE project_id = :pid
    ),
    renorm AS (
      UPDATE project_theme_weightings p
      SET weight_norm = CASE WHEN sumw.s > 0 THEN p.weight_raw / sumw.s ELSE 0 END
      FROM sumw
      WHERE p.project_id = :pid
      RETURNING p.theme_id, p.weight_norm
    )
    UPDATE runtime_scores r
    SET theme_weighted_effectiveness =
          COALESCE(r.adjusted_base_effectiveness, 0) * rn.weight_norm
    FROM interventions i
    JOIN renorm rn ON rn.theme_id = i.theme_id
    WHERE r.project_id = :pid
      AND i.id = r.intervention_id;
    """
    with _begin_tx(conn):
        conn.execute(
            text(sql),
            {"pid": project_id, "iid": intervention_id, "alpha": float(alpha), "floor": float(floor)},
        )
        return 1