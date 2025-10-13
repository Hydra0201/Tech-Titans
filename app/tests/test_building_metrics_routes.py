# tests/test_building_metrics_routes.py
import os
import pytest
from flask import Flask, url_for
from app import create_app

@pytest.fixture
def app():
    # Keep env consistent across tests
    os.environ.setdefault("JWT_SECRET", "test-secret")
    os.environ.setdefault("JWT_EXPIRES_HOURS", "1")

    app = create_app()
    app.config.update(TESTING=True)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_send_metrics_dry_run_accepts_wrapped_shape(client, app):
    """
    The route accepts {metrics:{...}} and should return dry_run=True.
    Use real metric keys so payload parsing succeeds.
    """
    with app.test_request_context():
        path = url_for("metrics.send_metrics", project_id=12345)

    r = client.post(
        path,
        query_string={"dry_run": 1},
        json={"metrics": {"levels": 3, "opening_pct": 45.5}},
    )
    assert r.status_code == 200, r.get_data(as_text=True)
    data = r.get_json()
    assert data["dry_run"] is True
    assert data["project_id"] == 12345
    assert "updated" in data  # count may be 0 if no rules/interventions seeded

def test_send_metrics_dry_run_accepts_raw_shape(client, app):
    """
    The route also accepts a raw metrics mapping without the 'metrics' wrapper.
    """
    with app.test_request_context():
        path = url_for("metrics.send_metrics", project_id=67890)

    r = client.post(
        path,
        query_string={"dry_run": "true"},
        json={"levels": 2, "wall_to_floor_ratio": 1.8},
    )
    assert r.status_code == 200, r.get_data(as_text=True)
    data = r.get_json()
    assert data["dry_run"] is True
    assert data["project_id"] == 67890
    assert "updated" in data

def test_send_metrics_invalid_payload_missing_metrics_key_when_wrapped(client, app):
    """
    When using the wrapped shape, missing 'metrics' should 400.
    """
    with app.test_request_context():
        path = url_for("metrics.send_metrics", project_id=111)

    resp = client.post(path, json={"foo": "bar"})
    assert resp.status_code == 400
    data = resp.get_json()
    assert "message" in data or "error" in data

def test_send_metrics_invalid_payload_non_numeric_values(client, app):
    """
    Non-numeric values should 400.
    """
    with app.test_request_context():
        path = url_for("metrics.send_metrics", project_id=222)

    resp = client.post(path, json={"metrics": {"levels": "three"}})
    assert resp.status_code == 400
    data = resp.get_json()
    # your route returns one of these keys
    assert ("message" in data) or ("error" in data)
