"""Unit tests for run/revision naming.

REQ: FLH-F-023
"""

from __future__ import annotations

from pathlib import Path

from formloop.store.naming import (
    next_revision_name,
    next_run_name,
    reserve_next_revision_name_dir,
    reserve_next_run_name_dir,
)


def test_next_run_name_empty(tmp_path: Path) -> None:
    assert next_run_name(tmp_path) == "run-0001"


def test_next_run_name_increments(tmp_path: Path) -> None:
    (tmp_path / "run-0001").mkdir()
    (tmp_path / "run-0003").mkdir()
    (tmp_path / "not-a-run").mkdir()
    assert next_run_name(tmp_path) == "run-0004"


def test_next_run_name_ignores_files(tmp_path: Path) -> None:
    (tmp_path / "run-0005").write_text("x")  # file, not dir
    assert next_run_name(tmp_path) == "run-0001"


def test_next_revision_name_empty(tmp_path: Path) -> None:
    assert next_revision_name(tmp_path) == "rev-001"


def test_next_revision_name_increments(tmp_path: Path) -> None:
    (tmp_path / "rev-001").mkdir()
    (tmp_path / "rev-002").mkdir()
    assert next_revision_name(tmp_path) == "rev-003"


def test_next_revision_name_handles_wide_indices(tmp_path: Path) -> None:
    (tmp_path / "rev-999").mkdir()
    # Pattern allows 3+ digits so 1000 is accepted, formatted with min-width 3
    assert next_revision_name(tmp_path) == "rev-1000"


def test_reserve_next_run_name_dir_creates_folder(tmp_path: Path) -> None:
    name = reserve_next_run_name_dir(tmp_path)
    assert name == "run-0001"
    assert (tmp_path / name).is_dir()


def test_reserve_next_revision_name_dir_creates_folder(tmp_path: Path) -> None:
    name = reserve_next_revision_name_dir(tmp_path)
    assert name == "rev-001"
    assert (tmp_path / name).is_dir()
