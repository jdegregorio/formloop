from __future__ import annotations

from fastapi.testclient import TestClient

from formloop.api.app import create_app


def test_api_can_submit_and_fetch_run(configured_env) -> None:
    app = create_app()
    client = TestClient(app)
    response = client.post("/runs", json={"prompt": "Create a block width 40 height 20 depth 10 for a mounting spacer."})
    assert response.status_code == 200
    payload = response.json()
    run_id = payload["run_id"]
    fetch = client.get(f"/runs/{run_id}")
    assert fetch.status_code == 200
    assert fetch.json()["run_id"] == run_id
    events = client.get(f"/runs/{run_id}/events")
    assert events.status_code == 200
    assert len(events.json()) >= 1

