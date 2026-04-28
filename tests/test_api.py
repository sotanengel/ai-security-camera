"""FastAPI event API contract tests."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ai_security_camera.api.app import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ASC_DATA_DIR", str(tmp_path / "d"))
    monkeypatch.setenv("ASC_API_TOKEN", "testtoken")
    with TestClient(app) as c:
        yield c


def test_health_unauthenticated(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_events_require_auth(client: TestClient) -> None:
    r = client.get("/v1/events")
    assert r.status_code == 401


def test_create_and_list_events(client: TestClient) -> None:
    h = {"Authorization": "Bearer testtoken"}
    payload = {
        "template_id": "uc_01",
        "detector_summary": "person 0.9",
        "vlm": {
            "event_type": "delivery",
            "confidence": 0.8,
            "description": "荷物",
            "objects": ["person"],
            "should_notify": True,
            "severity": "medium",
        },
    }
    r = client.post("/v1/events", json=payload, headers=h)
    assert r.status_code == 200
    eid = r.json()["id"]
    r2 = client.get("/v1/events", headers=h)
    assert r2.status_code == 200
    ids = [x["id"] for x in r2.json()]
    assert eid in ids
