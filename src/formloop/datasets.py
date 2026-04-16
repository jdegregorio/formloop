from __future__ import annotations

from pathlib import Path

import yaml

from formloop.models import EvalCase


def load_eval_cases(dataset_root: Path, dataset_name: str) -> list[EvalCase]:
    root = dataset_root / dataset_name
    if not root.exists():
        raise FileNotFoundError(f"Dataset not found: {root}")
    cases: list[EvalCase] = []
    for case_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        case_file = case_dir / "case.yaml"
        if not case_file.exists():
            continue
        payload = yaml.safe_load(case_file.read_text(encoding="utf-8"))
        payload["ground_truth_step"] = str((case_dir / payload["ground_truth_step"]).resolve())
        if payload.get("reference_image"):
            payload["reference_image"] = str((case_dir / payload["reference_image"]).resolve())
        cases.append(EvalCase.model_validate(payload))
    return cases

