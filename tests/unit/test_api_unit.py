from __future__ import annotations

from fastapi.testclient import TestClient

from formloop.api.app import create_app


def test_api_healthz_and_artifact_endpoints(configured_env) -> None:
    app = create_app()
    client = TestClient(app)

    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.json()["ok"] is True

    run = client.post("/runs", json={"prompt": "Create a block width 40 height 20 depth 10 for a mounting spacer."}).json()
    artifact = next(a for a in run["final_artifacts"] if a["kind"] == "step")
    response = client.get(f"/artifacts/{run['run_id']}/{artifact['path']}")
    assert response.status_code == 200

    stream = client.get(f"/runs/{run['run_id']}/events/stream")
    assert stream.status_code == 200
    assert "progress" in stream.text

    not_found = client.get("/artifacts/missing/nope.txt")
    assert not_found.status_code == 404

