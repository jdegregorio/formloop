from __future__ import annotations

import time

from fastapi.testclient import TestClient

from formloop.http.api import create_app
from formloop.models import NormalizedSpec, RunCreateRequest
from formloop.services.harness import HarnessService


class FakeApiHarness(HarnessService):
    async def continue_run(self, run_name: str, request: RunCreateRequest):
        run = self.store.load_run(run_name)
        run.current_spec = NormalizedSpec(intent_summary=request.prompt)
        snapshot = self._materialize_snapshot(run)
        self.store.write_snapshot(snapshot, run_name=run_name)
        return None


def test_flh_f_025_http_create_and_poll(test_config) -> None:
    app = create_app(FakeApiHarness(config=test_config))
    with TestClient(app) as client:
        response = client.post("/runs", json={"prompt": "Create a cube.", "profile": "dev_test"})
        assert response.status_code == 200
        payload = response.json()
        run_name = payload["run_name"]
        time.sleep(0.05)
        snapshot = client.get(f"/runs/{run_name}")
        assert snapshot.status_code == 200
        assert snapshot.json()["run_name"] == run_name
        events = client.get(f"/runs/{run_name}/events")
        assert events.status_code == 200
        assert len(events.json()) >= 1
