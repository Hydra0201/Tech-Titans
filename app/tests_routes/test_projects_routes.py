import uuid
import math
import pytest
import os
from sqlalchemy import text

from app import create_app, get_conn


@pytest.fixture
def app():
    import os
    os.environ["JWT_SECRET"] = "test-secret"        # force same secret
    os.environ["JWT_EXPIRES_HOURS"] = "1"
    app = create_app()
    app.config.update(TESTING=True)
    return app

@pytest.fixture
def client(app):
    return app.test_client()


# ---------- helpers ----------

def _cleanup(conn, project_id=None):
    if project_id:
        conn.execute(
            text("DELETE FROM project_theme_weightings WHERE project_id = :pid"),
            {"pid": project_id},
        )
        conn.execute(
            text("DELETE FROM projects WHERE id = :pid"),
            {"pid": project_id},
        )


def _auth_headers(client):
    """Ensure a test user exists and return valid Authorization headers."""
    email = "tester@example.com"
    password = "pass123"

    # Try to create the user (ignore conflict if already exists)
    client.post("/api/admin/users", json={
        "email": email,
        "password": password,
        "role": "Admin",
        "default_access_level": "edit",
        "name": "Tester",
    })

    # Now log in
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"Login failed: {r.get_data(as_text=True)}"

    token = r.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}



# ---------- tests ----------

def test_create_minimal_project_success(client, app):
    name = f"API Project {uuid.uuid4().hex[:6]}"
    r = client.post("/api/projects", json={"name": name}, headers=_auth_headers(client))
    assert r.status_code == 201, r.get_data(as_text=True)
    data = r.get_json()["project"]
    pid = data["id"]
    assert data["name"] == name

    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        try:
            _cleanup(conn, pid)
            tx.commit()
        except:
            tx.rollback()
            raise


def test_create_requires_name(client):
    r = client.post("/api/projects", json={}, headers=_auth_headers(client))
    assert r.status_code == 400


def test_get_project_not_found(client):
    r = client.get("/api/projects/987654321")
    assert r.status_code == 404


def test_patch_project_update_and_fetch(client, app):
    name = f"PatchMe {uuid.uuid4().hex[:6]}"
    r1 = client.post("/api/projects", json={"name": name}, headers=_auth_headers(client))
    assert r1.status_code == 201
    proj = r1.get_json()["project"]
    pid = proj["id"]

    payload = {
        "building_type": "Office",
        "location": "NYC",
        "levels": 5,
        "opening_pct": 12.5,
        "external_wall_area": 1234.56,
    }
    r2 = client.patch(f"/api/projects/{pid}", json=payload)
    assert r2.status_code == 200
    updated = r2.get_json()["project"]
    assert updated["building_type"] == "Office"
    assert updated["location"] == "NYC"
    assert updated["levels"] == 5
    assert math.isclose(updated["opening_pct"], 12.5, rel_tol=1e-9)
    assert math.isclose(updated["external_wall_area"], 1234.56, rel_tol=1e-9)

    r3 = client.get(f"/api/projects/{pid}")
    assert r3.status_code == 200
    fetched = r3.get_json()["project"]
    assert fetched["building_type"] == "Office"
    assert fetched["location"] == "NYC"
    assert fetched["levels"] == 5
    assert math.isclose(fetched["opening_pct"], 12.5, rel_tol=1e-9)
    assert math.isclose(fetched["external_wall_area"], 1234.56, rel_tol=1e-9)

    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        try:
            _cleanup(conn, pid)
            tx.commit()
        except:
            tx.rollback()
            raise


def test_patch_no_valid_fields_returns_400(client, app):
    r1 = client.post("/api/projects", json={"name": f"EmptyPatch {uuid.uuid4().hex[:6]}"}, headers=_auth_headers(client))
    assert r1.status_code == 201
    pid = r1.get_json()["project"]["id"]

    r2 = client.patch(f"/api/projects/{pid}", json={"unknown_key": 123})
    assert r2.status_code == 400

    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        try:
            _cleanup(conn, pid)
            tx.commit()
        except:
            tx.rollback()
            raise


def test_delete_project_then_404_on_get(client, app):
    r1 = client.post("/api/projects", json={"name": f"Deletable {uuid.uuid4().hex[:6]}"}, headers=_auth_headers(client))
    assert r1.status_code == 201
    pid = r1.get_json()["project"]["id"]

    r2 = client.delete(f"/api/projects/{pid}")
    assert r2.status_code == 200
    body = r2.get_json()
    assert body["deleted"] is True and body["id"] == pid

    r3 = client.get(f"/api/projects/{pid}")
    assert r3.status_code == 404


def test_create_with_extra_fields_ignored(client, app):
    name = f"IgnoreExtra {uuid.uuid4().hex[:6]}"
    r = client.post("/api/projects", json={"name": name, "foo": "bar"}, headers=_auth_headers(client))
    assert r.status_code == 201
    proj = r.get_json()["project"]
    pid = proj["id"]
    assert "foo" not in proj

    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        try:
            _cleanup(conn, pid)
            tx.commit()
        except:
            tx.rollback()
            raise


def test_create_with_numeric_fields_cast(client, app):
    name = f"NumFields {uuid.uuid4().hex[:6]}"
    payload = {
        "name": name,
        "levels": 3,
        "opening_pct": 7.25,
        "external_wall_area": 1000.2,
    }
    r = client.post("/api/projects", json=payload, headers=_auth_headers(client))
    assert r.status_code == 201
    proj = r.get_json()["project"]
    pid = proj["id"]
    assert proj["levels"] == 3
    assert isinstance(proj["opening_pct"], float)
    assert isinstance(proj["external_wall_area"], float)

    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        try:
            _cleanup(conn, pid)
            tx.commit()
        except:
            tx.rollback()
            raise
