from __future__ import annotations

import json
from pathlib import Path

import pytest

from formloop.evals.dataset import load_cases, resolve_dataset_path


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_load_cases_accepts_dataset_directory_and_resolves_relative_paths(tmp_path: Path) -> None:
    dataset = tmp_path / "basic_shapes"
    dataset.mkdir()
    (dataset / "ground_truth").mkdir()
    (dataset / "refs").mkdir()
    _write_jsonl(
        dataset / "cases.jsonl",
        [
            {
                "case_id": "cube",
                "prompt": "a cube",
                "ground_truth_step": "ground_truth/cube.step",
                "reference_image": "refs/cube.png",
            }
        ],
    )

    cases = load_cases(dataset)

    assert resolve_dataset_path(dataset) == dataset / "cases.jsonl"
    assert len(cases) == 1
    assert cases[0].case_id == "cube"
    assert cases[0].prompt == "a cube"
    assert cases[0].ground_truth_step == (dataset / "ground_truth/cube.step").resolve()
    assert cases[0].reference_image == (dataset / "refs/cube.png").resolve()


def test_load_cases_rejects_removed_spec_and_tags_fields(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    _write_jsonl(
        path,
        [
            {
                "case_id": "cube",
                "prompt": "a cube",
                "ground_truth_step": "cube.step",
                "spec": {"kind": "cube"},
                "tags": ["basic"],
            }
        ],
    )

    with pytest.raises(ValueError, match="removed eval case field"):
        load_cases(path)


def test_load_cases_rejects_duplicate_case_ids(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    _write_jsonl(
        path,
        [
            {"case_id": "cube", "prompt": "a cube", "ground_truth_step": "cube.step"},
            {"case_id": "cube", "prompt": "another cube", "ground_truth_step": "cube2.step"},
        ],
    )

    with pytest.raises(ValueError, match="duplicate case_id"):
        load_cases(path)


def test_load_cases_requires_ground_truth_step(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    _write_jsonl(path, [{"case_id": "cube", "prompt": "a cube"}])

    with pytest.raises(KeyError):
        load_cases(path)
