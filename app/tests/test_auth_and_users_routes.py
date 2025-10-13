# tests/test_auth_and_users.py
import os, uuid, pytest
from sqlalchemy import text
from passlib.context import CryptContext

from app import create_app, get_conn

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

@pytest.fixture
def app():
    # Ensure JWT is configured for the app under test
    os.environ.setdefault("JWT_SECRET", "test-secret")
    os.environ.setdefault("JWT_EXPIRES_HOURS", "1")
    app = create_app()
    app.config.update(TESTING=True)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def seed_admin(app):
    """
    Seed an Admin user directly into the DB and yield its creds.
    Clean up after tests.
    """
    email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    password = "AdminPass123!"
    pw_hash = pwd_ctx.hash(password)

    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        row = conn.execute(
            text("""
                INSERT INTO users (email, name, role, default_access_level, password_hash)
                VALUES (:email, 'Admin Tester', 'Admin', 'edit', :hash)
                RETURNING id
            """),
            {"email": email, "hash": pw_hash},
        ).mappings().one()
        admin_id = row["id"]
        tx.commit()

    yield {"id": admin_id, "email": email, "password": password}

    # cleanup
    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        conn.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": admin_id})
        tx.commit()

@pytest.fixture
def admin_token(client, seed_admin):
    """Login as the seeded Admin and return its JWT."""
    r = client.post("/api/auth/login", json={
        "email": seed_admin["email"],
        "password": seed_admin["password"],
    })
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert "access_token" in body
    return body["access_token"]

def _auth_hdr(token: str):
    return {"Authorization": f"Bearer {token}"}

# -----------------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------------

def test_login_missing_fields(client):
    r = client.post("/api/auth/login", json={"email": ""})
    assert r.status_code == 400

def test_create_user_invalid_email(client, admin_token):
    payload = {
        "name": "Bad Email",
        "email": "not-an-email",
        "password": "Passw0rd!",
        "role": "Employee",
        "default_access_level": "view",
    }
    r = client.post("/api/admin/users", json=payload, headers=_auth_hdr(admin_token))
    assert r.status_code == 400
    assert r.get_json()["error"] == "invalid_email"

def test_create_user_success_and_duplicate(client, app, admin_token):
    email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "name": "Dup User",
        "email": email,
        "password": "Passw0rd!",
        "role": "Employee",
        "default_access_level": "view",
    }

    # Create (authorized)
    r1 = client.post("/api/admin/users", json=payload, headers=_auth_hdr(admin_token))
    assert r1.status_code == 201, r1.get_data(as_text=True)

    # Duplicate email should 409
    r2 = client.post("/api/admin/users", json=payload, headers=_auth_hdr(admin_token))
    assert r2.status_code == 409

    # cleanup
    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        conn.execute(text("DELETE FROM users WHERE email = :email"), {"email": email})
        tx.commit()

def test_admin_users_requires_auth_now(client):
    # Missing token -> 401
    payload = {
        "name": "NoAuth",
        "email": f"noauth_{uuid.uuid4().hex[:8]}@example.com",
        "password": "Passw0rd!",
        "role": "Employee",
        "default_access_level": "view",
    }
    r = client.post("/api/admin/users", json=payload)
    assert r.status_code in (401, 403)  # depending on your guard

def test_login_ok_and_bad_password(client, seed_admin):
    # OK
    r_ok = client.post("/api/auth/login", json={
        "email": seed_admin["email"],
        "password": seed_admin["password"],
    })
    assert r_ok.status_code == 200
    body = r_ok.get_json()
    assert "user" in body and body["user"]["email"] == seed_admin["email"]
    assert "access_token" in body

    # bad password
    r_bad = client.post("/api/auth/login", json={"email": seed_admin["email"], "password": "wrong"})
    assert r_bad.status_code == 401
