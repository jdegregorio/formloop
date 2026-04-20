"""Unit tests for safe artifact I/O.

REQ: FLH-V-001, FLH-D-004
"""

from __future__ import annotations

from pathlib import Path

import pytest

from formloop.runtime.artifacts import ArtifactPathError, read_artifact, write_artifact
from formloop.runtime.constrained_python import write_model_source


def test_write_and_read_text(tmp_path: Path) -> None:
    p = write_artifact(tmp_path, "sub/dir/file.txt", "hello")
    assert p.read_text() == "hello"
    assert read_artifact(tmp_path, "sub/dir/file.txt") == "hello"


def test_write_binary(tmp_path: Path) -> None:
    data = b"\x00\x01\x02"
    p = write_artifact(tmp_path, "bin.dat", data)
    assert read_artifact(tmp_path, p.name, binary=True) == data


def test_escape_root_rejected(tmp_path: Path) -> None:
    with pytest.raises(ArtifactPathError):
        write_artifact(tmp_path, "../escape.txt", "bad")


def test_absolute_path_outside_root_rejected(tmp_path: Path) -> None:
    # Use a path that resolves outside tmp_path
    outside = tmp_path.parent / "sibling.txt"
    with pytest.raises(ArtifactPathError):
        write_artifact(tmp_path, outside, "bad")


def test_read_missing_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_artifact(tmp_path, "nope.txt")


def test_write_model_source_lands_in_inputs(tmp_path: Path) -> None:
    source = "def build_model(params, context):\n    return None\n"
    p = write_model_source(tmp_path, source)
    assert p.name == "model.py"
    assert p.read_text() == source
