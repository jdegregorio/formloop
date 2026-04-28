"""Eval case loader (FLH-F-014, FLH-NF-003)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

CASES_FILENAME = "cases.jsonl"
REMOVED_FIELDS = frozenset(("spec", "tags"))


@dataclass
class EvalCase:
    case_id: str
    prompt: str
    ground_truth_step: Path
    reference_image: Path | None = None
    source_line: int = field(default=0)


def resolve_dataset_path(dataset_path: Path) -> Path:
    """Resolve a dataset directory or direct JSONL path to ``cases.jsonl``."""

    if dataset_path.is_dir():
        dataset_path = dataset_path / CASES_FILENAME
    if not dataset_path.is_file():
        raise FileNotFoundError(f"dataset not found: {dataset_path}")
    return dataset_path


def load_cases(dataset_path: Path) -> list[EvalCase]:
    """Load eval cases from a dataset directory or direct ``cases.jsonl`` path."""

    dataset_path = resolve_dataset_path(dataset_path)
    cases: list[EvalCase] = []
    base = dataset_path.parent
    seen: set[str] = set()
    for line_number, line in enumerate(dataset_path.read_text().splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        removed = sorted(REMOVED_FIELDS.intersection(row))
        if removed:
            names = ", ".join(removed)
            raise ValueError(
                f"{dataset_path}:{line_number}: removed eval case field(s): {names}"
            )
        case_id = str(row["case_id"])
        if case_id in seen:
            raise ValueError(f"{dataset_path}:{line_number}: duplicate case_id {case_id!r}")
        seen.add(case_id)
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
                case_id=case_id,
                prompt=str(row["prompt"]),
                ground_truth_step=gt,
                reference_image=ref_path,
                source_line=line_number,
            )
        )
    return cases
