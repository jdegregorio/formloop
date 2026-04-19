"""Filesystem persistence for run and revision state."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

from filelock import FileLock

from .jsonutil import dumps_json
from .models import (
    ProgressEvent,
    RevisionRecord,
    RunCreateRequest,
    RunRecord,
    RunSnapshot,
    RunStatus,
)


class RunStore:
    """Filesystem-first persistence model for `run > revision`."""

    # Req: FLH-F-011, FLH-F-021, FLH-F-022, FLH-F-023, FLH-D-023, FLH-NF-002

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._name_lock = FileLock(str(self.root / ".naming.lock"))

    def _next_ordinal(self, prefix: str) -> int:
        ordinals: list[int] = []
        for child in self.root.iterdir():
            if not child.is_dir() or not child.name.startswith(prefix):
                continue
            suffix = child.name.removeprefix(prefix)
            if suffix.isdigit():
                ordinals.append(int(suffix))
        return (max(ordinals) if ordinals else 0) + 1

    def next_run_name(self) -> str:
        with self._name_lock:
            return f"run-{self._next_ordinal('run-'):06d}"

    def next_revision_name(self, run_dir: Path) -> tuple[str, int]:
        revisions_dir = run_dir / "revisions"
        revisions_dir.mkdir(parents=True, exist_ok=True)
        ordinals: list[int] = []
        for child in revisions_dir.iterdir():
            if not child.is_dir() or not child.name.startswith("rev-"):
                continue
            suffix = child.name.removeprefix("rev-")
            if suffix.isdigit():
                ordinals.append(int(suffix))
        ordinal = (max(ordinals) if ordinals else 0) + 1
        return f"rev-{ordinal:03d}", ordinal

    def run_dir(self, run_name: str) -> Path:
        return self.root / run_name

    def create_run(
        self,
        request: RunCreateRequest,
        *,
        input_summary: str,
        current_spec: Any,
        effective_profile: str,
        effective_model: str,
        effective_reasoning: str,
    ) -> RunRecord:
        run_name = self.next_run_name()
        run_id = f"{run_name}-{uuid4().hex[:8]}"
        run_dir = self.run_dir(run_name)
        (run_dir / "inputs").mkdir(parents=True, exist_ok=True)
        (run_dir / "research").mkdir(parents=True, exist_ok=True)
        (run_dir / "revisions").mkdir(parents=True, exist_ok=True)
        record = RunRecord(
            run_id=run_id,
            run_name=run_name,
            prompt=request.prompt,
            input_summary=input_summary,
            reference_image=request.reference_image,
            effective_profile=effective_profile,
            effective_model=effective_model,
            effective_reasoning=effective_reasoning,
            current_spec=current_spec,
            current_status_summary="Run created",
            status=RunStatus.created,
        )
        self.write_run(record)
        self.write_snapshot(
            RunSnapshot(
                run_id=record.run_id,
                run_name=record.run_name,
                status=record.status,
                current_spec_summary=input_summary,
            ),
            run_name=run_name,
        )
        (run_dir / "inputs" / "request.json").write_text(
            dumps_json(request.model_dump(mode="json")),
            encoding="utf-8",
        )
        return record

    def create_revision(
        self,
        *,
        run: RunRecord,
        trigger: str,
    ) -> tuple[RevisionRecord, Path]:
        run_dir = self.run_dir(run.run_name)
        revision_name, ordinal = self.next_revision_name(run_dir)
        revision_dir = run_dir / "revisions" / revision_name
        (revision_dir / "views").mkdir(parents=True, exist_ok=True)
        (revision_dir / "workspace").mkdir(parents=True, exist_ok=True)
        revision = RevisionRecord(
            revision_id=f"{revision_name}-{uuid4().hex[:8]}",
            revision_name=revision_name,
            ordinal=ordinal,
            trigger=trigger,
            status="in_progress",
            spec_snapshot=run.current_spec,
            artifact_manifest_path=str(revision_dir / "artifact-manifest.json"),
            workspace_path=str(revision_dir / "workspace"),
        )
        self.write_revision(run.run_name, revision)
        return revision, revision_dir

    def write_run(self, run: RunRecord) -> None:
        path = self.run_dir(run.run_name) / "run.json"
        path.write_text(run.model_dump_json(indent=2), encoding="utf-8")

    def load_run(self, run_name: str) -> RunRecord:
        path = self.run_dir(run_name) / "run.json"
        return RunRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def write_snapshot(self, snapshot: RunSnapshot, *, run_name: str) -> None:
        path = self.run_dir(run_name) / "snapshot.json"
        path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")

    def load_snapshot(self, run_name: str) -> RunSnapshot:
        path = self.run_dir(run_name) / "snapshot.json"
        return RunSnapshot.model_validate_json(path.read_text(encoding="utf-8"))

    def append_event(self, run_name: str, event: ProgressEvent) -> None:
        events_path = self.run_dir(run_name) / "events.jsonl"
        with events_path.open("a", encoding="utf-8") as handle:
            handle.write(event.model_dump_json())
            handle.write("\n")

    def list_events(self, run_name: str) -> list[ProgressEvent]:
        events_path = self.run_dir(run_name) / "events.jsonl"
        if not events_path.exists():
            return []
        return [
            ProgressEvent.model_validate_json(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def write_revision(self, run_name: str, revision: RevisionRecord) -> None:
        revision_dir = self.run_dir(run_name) / "revisions" / revision.revision_name
        revision_dir.mkdir(parents=True, exist_ok=True)
        (revision_dir / "revision.json").write_text(
            revision.model_dump_json(indent=2), encoding="utf-8"
        )

    def write_json_file(self, path: Path, payload: Any) -> None:
        if hasattr(payload, "model_dump_json"):
            data = payload.model_dump_json(indent=2)
        else:
            data = json.dumps(payload, indent=2, sort_keys=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding="utf-8")

    def copy_into_revision(self, source: Path, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
