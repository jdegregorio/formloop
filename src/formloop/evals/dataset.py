"""Eval case loader (FLH-F-014, FLH-NF-003)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EvalCase:
    case_id: str
    prompt: str
    spec: dict
    ground_truth_step: Path
    reference_image: Path | None = None
    tags: list[str] = field(default_factory=list)


def load_cases(dataset_path: Path) -> list[EvalCase]:
    """Load cases.jsonl. ``dataset_path`` points at the JSONL file itself."""

    if not dataset_path.is_file():
        raise FileNotFoundError(f"dataset not found: {dataset_path}")
    cases: list[EvalCase] = []
    base = dataset_path.parent
    for line in dataset_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        gt = Path(row["ground_truth_step"])
        if not gt.is_absolute():
            gt = (base / gt).resolve()
        ref = row.get("reference_image")
        ref_path: Path | None = None
        if ref:
            rp = Path(ref)
            ref_path = rp if rp.is_absolute() else (base / rp).resolve()
        cases.append(
            EvalCase(
                case_id=row["case_id"],
                prompt=row["prompt"],
                spec=row.get("spec", {}),
                ground_truth_step=gt,
                reference_image=ref_path,
                tags=row.get("tags", []),
            )
        )
    return cases
