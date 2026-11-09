import time

from fastapi.testclient import TestClient
import numpy as np
import pytest

from attendance_camera.app import create_app
from attendance_camera.config import Settings


def configured(tmp_path, **extra):
    return Settings(database=tmp_path / "counts.sqlite3", allowed_hosts=["testserver"], **extra)


def fresh(app):
    app.state.runtime.process([], np.zeros((100, 100, 3), dtype=np.uint8), time.monotonic())


def test_session_lifecycle_and_csv(tmp_path):
    app = create_app(configured(tmp_path), start_worker=False)
    with TestClient(app) as client:
        assert client.get("/readyz").status_code == 503
        assert client.post("/api/sessions", json={"occupancy": 0}).status_code == 409
        fresh(app)
        assert client.put("/api/calibration", json={}).status_code == 200
        assert client.get("/readyz").status_code == 200
        result = client.post("/api/sessions", json={"occupancy": 4})
        assert result.status_code == 201
        assert client.post("/api/sessions", json={"occupancy": 0}).status_code == 409
        app.state.store.record(2, 1)
        assert client.get("/api/status").json()["session"]["occupancy"] == 5
        assert client.post("/api/session/reconcile", json={"occupancy": 3}).json()["occupancy"] == 3
        export = client.get(f"/api/sessions/{result.json()['id']}/counts.csv")
        assert export.status_code == 200 and "incoming,outgoing,correction,occupancy" in export.text
        assert client.get("/api/preview.jpg").headers["cache-control"] == "no-store"
        app.state.runtime.gap("test disconnect")
        assert client.get("/api/preview.jpg").status_code == 503
        assert client.get("/readyz").status_code == 503
        assert client.get("/api/status").json()["session"]["needs_reconciliation"]
        client.post("/api/session/end")
        assert client.get("/api/status").json()["session"] is None


def test_auth_csrf_and_host_validation(tmp_path):
    token = "test-token-with-at-least-24-characters"
    app = create_app(configured(tmp_path, token=token), start_worker=False)
    with TestClient(app) as client:
        assert client.get("/healthz").status_code == 200
        for path in ("/", "/api/status", "/api/preview.jpg", "/openapi.json"):
            assert client.get(path).status_code == 401
        assert client.get("/api/status", auth=("organizer", "incorrect")).status_code == 401
        assert (
            client.get(
                "/api/status", headers={"Authorization": "Basic w7ZyZ2FuaXplcjp0ZXN0"}
            ).status_code
            == 401
        )
        assert client.get("/api/status", auth=("organizer", token)).status_code == 200
        assert (
            client.put(
                "/api/calibration",
                json={},
                auth=("organizer", token),
                headers={"Origin": "https://evil.example"},
            ).status_code
            == 403
        )
        assert (
            client.get(
                "/api/status", auth=("organizer", token), headers={"Host": "evil.example"}
            ).status_code
            == 400
        )


def test_remote_binding_requires_password():
    with pytest.raises(ValueError):
        Settings(host="0.0.0.0")


def test_restart_marks_existing_session_uncertain(tmp_path):
    settings = configured(tmp_path)
    first = create_app(settings, start_worker=False)
    with TestClient(first):
        first.state.store.start(7)
    second = create_app(settings, start_worker=False)
    with TestClient(second) as client:
        session = client.get("/api/status").json()["session"]
        assert session["occupancy"] == 7 and session["needs_reconciliation"]
