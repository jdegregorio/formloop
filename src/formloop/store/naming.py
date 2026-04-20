"""Human-readable sequential naming for runs and revisions.

REQ: FLH-F-023
"""

from __future__ import annotations

import re
from pathlib import Path

RUN_PATTERN = re.compile(r"^run-(\d{4,})$")
REVISION_PATTERN = re.compile(r"^rev-(\d{3,})$")


def _max_index(parent: Path, pattern: re.Pattern[str]) -> int:
    if not parent.is_dir():
        return 0
    highest = 0
    for entry in parent.iterdir():
        if not entry.is_dir():
            continue
        m = pattern.match(entry.name)
        if m:
            highest = max(highest, int(m.group(1)))
    return highest


def next_run_name(runs_root: Path) -> str:
    """Return the next sequential run name, e.g. ``run-0001``."""

    idx = _max_index(runs_root, RUN_PATTERN) + 1
    return f"run-{idx:04d}"


def next_revision_name(revisions_dir: Path) -> str:
    """Return the next sequential revision name, e.g. ``rev-001``."""

    idx = _max_index(revisions_dir, REVISION_PATTERN) + 1
    return f"rev-{idx:03d}"
