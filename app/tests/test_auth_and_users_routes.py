# tests/test_auth_and_users.py
import os, uuid, pytest
from sqlalchemy import text
from app import create_app, get_conn

@pytest.fixture
def app():
    os.environ.setdefault("JWT_SECRET", "test-secret")        # <- add
    os.environ.setdefault("JWT_EXPIRES_HOURS", "1")           # <- optional, keeps tokens short-lived in tests
    app = create_app()
    app.config.update(TESTING=True)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def temp_user(client, app):
    """
    Create a temporary user via the API (no JWT required now) and delete after.
    """
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "Passw0rd!"
    payload = {
        "name": "Test User",
        "email": email,
        "password": password,
        "role": "Employee",
        "default_access_level": "view",
    }
    r = client.post("/api/admin/users", json=payload)
    assert r.status_code == 201, r.get_data(as_text=True)
    user = r.get_json()["user"]
    yield {"id": user["id"], "email": email, "password": password}

    # cleanup
    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        conn.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user["id"]})
        tx.commit()

# -------- tests: /admin/users (no auth now) --------

def test_create_user_success_and_duplicate(client, app):
    email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "name": "Dup User",
        "email": email,
        "password": "Passw0rd!",
        "role": "Employee",
        "default_access_level": "view",
    }

    r1 = client.post("/api/admin/users", json=payload)
    assert r1.status_code == 201, r1.get_data(as_text=True)

    # Duplicate email should 409
    r2 = client.post("/api/admin/users", json=payload)
    assert r2.status_code == 409

    # cleanup
    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        conn.execute(text("DELETE FROM users WHERE email = :email"), {"email": email})
        tx.commit()

# -------- tests: /auth/login (no JWT returned) --------

def test_login_missing_fields(client):
    r = client.post("/api/auth/login", json={"email": ""})
    assert r.status_code == 400

def test_create_user_invalid_email(client):
    payload = {
        "name": "Bad Email",
        "email": "not-an-email",
        "password": "Passw0rd!",
        "role": "Employee",
        "default_access_level": "view",
    }
    r = client.post("/api/admin/users", json=payload)
    assert r.status_code == 400
    assert r.get_json()["error"] == "invalid_email"

    
def test_login_ok_and_bad_password(client, temp_user):
    # OK
    r_ok = client.post("/api/auth/login", json={"email": temp_user["email"], "password": temp_user["password"]})
    assert r_ok.status_code == 200
    body = r_ok.get_json()
    assert "user" in body and body["user"]["email"] == temp_user["email"]
    assert "access_token" in body and body["user"]["email"] == temp_user["email"]

    # bad password
    r_bad = client.post("/api/auth/login", json={"email": temp_user["email"], "password": "wrong"})
    assert r_bad.status_code == 401


