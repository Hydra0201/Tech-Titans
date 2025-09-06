# app/tests/test_theme_weights_routes.py
import uuid
import math
import pytest
from sqlalchemy import text

from app import create_app, get_conn

@pytest.fixture
def app():
    app = create_app()
    app.config.update(TESTING=True)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

# ---------- helpers ----------

def _mk_project(conn, name_prefix="Test Project"):
    row = conn.execute(
        text("""INSERT INTO projects (name) VALUES (:n) RETURNING id"""),
        {"n": f"{name_prefix} {uuid.uuid4().hex[:6]}"},
    ).mappings().one()
    return row["id"]

def _mk_themes(conn, n=3, prefix="Theme"):
    ids = []
    for i in range(n):
        row = conn.execute(
            text("""INSERT INTO themes (name, description)
                    VALUES (:n, :d) RETURNING id"""),
            {
                "n": f"{prefix} {i+1} {uuid.uuid4().hex[:6]}",
                "d": f"Desc {i+1}",
            },
        ).mappings().one()
        ids.append(row["id"])
    return ids

def _cleanup(conn, project_id=None, theme_ids=None):
    if project_id:
        conn.execute(text("""DELETE FROM project_theme_scores WHERE project_id = :pid"""), {"pid": project_id})
        conn.execute(text("""DELETE FROM projects WHERE id = :pid"""), {"pid": project_id})
    if theme_ids:
        # delete any scores referencing these themes first (safety)
        conn.execute(
            text("""DELETE FROM project_theme_scores WHERE theme_id = ANY(:tids)"""),
            {"tids": theme_ids},
        )
        conn.execute(
            text("""DELETE FROM themes WHERE id = ANY(:tids)"""),
            {"tids": theme_ids},
        )

# ---------- tests ----------

def test_list_themes_ok(client, app):
    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        try:
            theme_ids = _mk_themes(conn, n=2, prefix="LT-Theme")
            tx.commit()
        except:
            tx.rollback()
            raise

    r = client.get("/api/themes")
    assert r.status_code == 200
    body = r.get_json()
    assert "themes" in body and isinstance(body["themes"], list)
    returned_ids = {t["id"] for t in body["themes"]}
    assert set(theme_ids).issubset(returned_ids)

    # cleanup
    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        try:
            _cleanup(conn, theme_ids=theme_ids)
            tx.commit()
        except:
            tx.rollback()
            raise

def test_upsert_theme_scores_dry_run(client, app):
    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        try:
            pid = _mk_project(conn, "DRY-PROJ")
            tids = _mk_themes(conn, n=3, prefix="DRY-THEME")
            tx.commit()
        except:
            tx.rollback()
            raise

    payload = {"weights": {str(tids[0]): 5, str(tids[1]): 3, str(tids[2]): 2}}
    r = client.post(f"/api/projects/{pid}/themes?dry_run=1", json=payload)
    assert r.status_code == 200
    body = r.get_json()
    assert body["dry_run"] is True
    assert body["updated"] == 3
    assert body["sum_raw"] == 10

    # Should NOT be persisted due to dry_run
    r2 = client.get(f"/api/projects/{pid}/theme-scores")
    assert r2.status_code == 200
    data = r2.get_json()["themes"]
    # For created themes, raw/normalized should be null
    by_id = {row["id"]: row for row in data if row["id"] in tids}
    assert all(by_id[t]["raw_weight"] is None for t in tids)
    assert all(by_id[t]["normalized_weight"] is None for t in tids)

    # cleanup
    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        try:
            _cleanup(conn, project_id=pid, theme_ids=tids)
            tx.commit()
        except:
            tx.rollback()
            raise

def test_upsert_commit_and_fetch_then_overwrite(client, app):
    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        try:
            pid = _mk_project(conn, "COMMIT-PROJ")
            tids = _mk_themes(conn, n=2, prefix="COMMIT-THEME")  # two themes
            tx.commit()
        except:
            tx.rollback()
            raise

    # First save: 2 : 1  -> normalized 2/3 and 1/3
    r = client.post(
        f"/api/projects/{pid}/themes",
        json={"weights": {str(tids[0]): 2, str(tids[1]): 1}},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["updated"] == 2
    assert math.isclose(body["sum_raw"], 3.0, rel_tol=1e-9)
    assert math.isclose(body["normalized"][str(tids[0])], 2/3, rel_tol=1e-9)
    assert math.isclose(body["normalized"][str(tids[1])], 1/3, rel_tol=1e-9)

    # Fetch and verify persisted
    r2 = client.get(f"/api/projects/{pid}/theme-scores")
    assert r2.status_code == 200
    themelist = r2.get_json()["themes"]
    m = {row["id"]: row for row in themelist if row["id"] in tids}
    assert math.isclose(float(m[tids[0]]["normalized_weight"]), 2/3, rel_tol=1e-9)
    assert math.isclose(float(m[tids[1]]["normalized_weight"]), 1/3, rel_tol=1e-9)

    # Overwrite with equal weights 1:1 -> 0.5 each (upsert path)
    r3 = client.post(
        f"/api/projects/{pid}/themes",
        json={"weights": {str(tids[0]): 1, str(tids[1]): 1}},
    )
    assert r3.status_code == 200
    b3 = r3.get_json()
    assert b3["updated"] == 2
    assert math.isclose(b3["sum_raw"], 2.0, rel_tol=1e-9)
    assert math.isclose(b3["normalized"][str(tids[0])], 0.5, rel_tol=1e-9)
    assert math.isclose(b3["normalized"][str(tids[1])], 0.5, rel_tol=1e-9)

    r4 = client.get(f"/api/projects/{pid}/theme-scores")
    assert r4.status_code == 200
    m2 = {row["id"]: row for row in r4.get_json()["themes"] if row["id"] in tids}
    assert math.isclose(float(m2[tids[0]]["normalized_weight"]), 0.5, rel_tol=1e-9)
    assert math.isclose(float(m2[tids[1]]["normalized_weight"]), 0.5, rel_tol=1e-9)

    # cleanup
    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        try:
            _cleanup(conn, project_id=pid, theme_ids=tids)
            tx.commit()
        except:
            tx.rollback()
            raise

def test_upsert_invalid_payload(client, app):
    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        try:
            pid = _mk_project(conn, "BADPAY-PROJ")
            tid = _mk_themes(conn, n=1, prefix="BADPAY-THEME")[0]
            tx.commit()
        except:
            tx.rollback()
            raise

    # missing weights
    r1 = client.post(f"/api/projects/{pid}/themes", json={})
    assert r1.status_code == 400

    # weights not a dict
    r2 = client.post(f"/api/projects/{pid}/themes", json={"weights": [1, 2, 3]})
    assert r2.status_code == 400

    # invalid number
    r3 = client.post(f"/api/projects/{pid}/themes", json={"weights": {str(tid): "abc"}})
    assert r3.status_code == 400

    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        try:
            _cleanup(conn, project_id=pid, theme_ids=[tid])
            tx.commit()
        except:
            tx.rollback()
            raise
