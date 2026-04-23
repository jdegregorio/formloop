"""Revision bundle input model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..schemas import RevisionTrigger


@dataclass
class CandidateBundle:
    """Inputs used to persist a revision."""

    trigger: RevisionTrigger
    spec_snapshot: dict[str, Any]
    designer_notes: str | None
    known_risks: list[str]
    model_py_src: Path
    step_src: Path
    glb_src: Path
    views_dir_src: Path
    render_sheet_src: Path
    build_metadata_src: Path | None = None
    render_metadata_src: Path | None = None
    inspect_summary_src: Path | None = None
