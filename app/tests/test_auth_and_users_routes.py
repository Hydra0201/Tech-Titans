import os, uuid, pytest
from sqlalchemy import text
from app import create_app, get_conn
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

@pytest.fixture
def app():
    app = create_app()
    app.config.update(TESTING=True)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def unique_email():
    """Generate a unique email for each test"""
    return f"test_{uuid.uuid4().hex[:12]}@example.com"

@pytest.fixture
def cleanup_user(app):
    """Cleanup fixture to remove test users"""
    users_to_cleanup = []
    
    yield users_to_cleanup
    
    # Cleanup after test
    with app.app_context():
        conn = get_conn()
        tx = conn.begin()
        for email in users_to_cleanup:
            conn.execute(text("DELETE FROM users WHERE email = :email"), {"email": email})
        tx.commit()

def test_create_user_success_and_duplicate(client, app, unique_email, cleanup_user):
    """
    POST /admin/users — create a user and test duplicate prevention.
    """
    cleanup_user.append(unique_email)  # Add to cleanup list
    
    payload = {
        "name": "Test User",
        "email": unique_email,
        "password": "Passw0rd!",
        "role": "Employee",
        "default_access_level": "view",
    }

    # First creation should succeed
    r1 = client.post("/api/admin/users", json=payload)
    assert r1.status_code == 201, f"First creation failed: {r1.get_data(as_text=True)}"

    # Duplicate email should fail with 409
    r2 = client.post("/api/admin/users", json=payload)
    assert r2.status_code == 409, f"Duplicate should fail: {r2.get_data(as_text=True)}"
    assert r2.get_json