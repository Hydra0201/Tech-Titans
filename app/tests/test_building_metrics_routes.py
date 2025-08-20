import os, pytest
from flask import Flask, url_for
from sqlalchemy import create_engine
from app.routes.building_metrics import metrics_bp
from app import create_app

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(TESTING=True)
    app = create_app()

    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_send_metrics_dry_run_hits_real_db(client):
    r = client.post(
        "/api/projects/1/metrics",
        query_string={"dry_run": 1},
        json={"metrics": {"1": 10, "2": 20}},
    )
    assert r.status_code == 200
    assert r.get_json()["dry_run"] is True

def test_send_metrics_invalid_payload(client, app):
    with app.test_request_context():
        path = url_for("metrics.send_metrics", project_id=123)


    # Payload missing "metrics"
    payload = {"foo": "bar"}
    resp = client.post(path, json = payload)

    assert resp.status_code == 400
    data = resp.get_json()
    assert "message" in data or "error" in data