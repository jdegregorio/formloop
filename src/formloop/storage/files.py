from __future__ import annotations

import json
from pathlib import Path

from formloop.models import RunRecord, TraceEvent


class FileRunStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.runs_dir = root / "runs"
        self.evals_dir = root / "evals"
        self.server_dir = root / "server"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.evals_dir.mkdir(parents=True, exist_ok=True)
        self.server_dir.mkdir(parents=True, exist_ok=True)

    def run_dir(self, run_id: str) -> Path:
        return self.runs_dir / run_id

    def create_run(self, record: RunRecord) -> Path:
        run_dir = self.run_dir(record.run_id)
        (run_dir / "revisions").mkdir(parents=True, exist_ok=True)
        self.save_run(record)
        return run_dir

    def save_run(self, record: RunRecord) -> None:
        run_dir = self.run_dir(record.run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        with (run_dir / "run.json").open("w", encoding="utf-8") as handle:
            handle.write(record.model_dump_json(indent=2))

    def load_run(self, run_id: str) -> RunRecord:
        run_dir = self.run_dir(run_id)
        with (run_dir / "run.json").open("r", encoding="utf-8") as handle:
            return RunRecord.model_validate_json(handle.read())

    def append_event(self, run_id: str, event: TraceEvent) -> None:
        run_dir = self.run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        with (run_dir / "events.ndjson").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(mode="json")) + "\n")

    def list_runs(self) -> list[str]:
        return sorted(path.name for path in self.runs_dir.iterdir() if path.is_dir())

