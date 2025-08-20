import pytest
from flask import Flask, url_for
from app.routes.building_metrics import metrics_bp
from unittest.mock import MagicMock

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(TESTING=True)
    app.register_blueprint(metrics_bp, url_prefix="/api")
    app.config["PG_CONN"] = MagicMock() # Mock DB conn
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_send_metrics_success(client, app):
    mock_conn = app.config["PG_CONN"]
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    payload = {"metrics": {"1": 10.0, "2": 20.0}}

    with app.test_request_context():
        path = url_for("metrics.send_metrics", project_id=123)

    resp = client.post(path, json=payload)

    if resp.status_code != 200:
        print("==== URL MAP ====")
        for r in app.url_map.iter_rules():
            print(r, "->", r.endpoint, r.methods)
        print("==== RESPONSE ====")
        print(resp.data.decode())

    assert resp.status_code == 200

def test_send_metrics_invalid_payload(client, app):
    with app.test_request_context():
        path = url_for("metrics.send_metrics", project_id=123)


    # Payload missing "metrics"
    payload = {"foo": "bar"}
    resp = client.post(path, json = payload)

    assert resp.status_code == 400
    data = resp.get_json()
    assert "message" in data or "error" in data