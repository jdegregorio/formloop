"""Append-only progress-event persistence helpers.

REQ: FLH-NF-006, FLH-NF-007
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..schemas import ProgressEvent, ProgressEventKind
from .layout import RunLayout


def atomic_append_line(path: Path, line: str) -> None:
    """Append a single line atomically (best effort)."""

    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = ""
    if path.is_file() and path.stat().st_size > 0:
        with path.open("rb") as fh:
            fh.seek(-1, os.SEEK_END)
            if fh.read(1) != b"\n":
                prefix = "\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(prefix + line.rstrip("\n") + "\n")


class EventLog:
    """Read/write/index helpers for ``events.jsonl``."""

    def next_index(self, layout: RunLayout) -> int:
        if not layout.events_jsonl.is_file():
            return 0
        with layout.events_jsonl.open("rb") as fh:
            try:
                fh.seek(-2, os.SEEK_END)
            except OSError:
                fh.seek(0)
            while fh.read(1) != b"\n":
                if fh.tell() <= 1:
                    fh.seek(0)
                    break
                fh.seek(-2, os.SEEK_CUR)
            last = fh.readline().decode("utf-8").strip()
        if not last:
            return self._line_count(layout)
        try:
            return int(json.loads(last)["index"]) + 1
        except Exception:
            return self._line_count(layout)

    def append(self, layout: RunLayout, event: ProgressEvent) -> ProgressEvent:
        assigned = event
        if assigned.index == 0 and layout.events_jsonl.is_file():
            assigned = assigned.model_copy(update={"index": self.next_index(layout)})
        atomic_append_line(layout.events_jsonl, assigned.model_dump_json())
        return assigned

    def read(self, layout: RunLayout, *, since: int = 0) -> list[ProgressEvent]:
        if not layout.events_jsonl.is_file():
            return []
        events: list[ProgressEvent] = []
        with layout.events_jsonl.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                ev = ProgressEvent.model_validate_json(line)
                if ev.index >= since:
                    events.append(ev)
        return events

    def find_latest_narration(
        self, layout: RunLayout, last_event: ProgressEvent | None
    ) -> ProgressEvent | None:
        if last_event is not None and last_event.kind is ProgressEventKind.narration:
            return last_event
        if not layout.events_jsonl.is_file():
            return None

        latest: ProgressEvent | None = None
        with layout.events_jsonl.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or '"narration"' not in line:
                    continue
                try:
                    ev = ProgressEvent.model_validate_json(line)
                except Exception:
                    continue
                if ev.kind is ProgressEventKind.narration:
                    latest = ev
        return latest

    @staticmethod
    def _line_count(layout: RunLayout) -> int:
        with layout.events_jsonl.open(encoding="utf-8") as fh:
            return sum(1 for _ in fh)
