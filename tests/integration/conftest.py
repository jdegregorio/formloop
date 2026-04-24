"""Shared fixtures for integration tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def cad_cli_root(repo_root: Path) -> Path:
    return repo_root.parent / "cad-cli"


@pytest.fixture(scope="session")
def cube_model(cad_cli_root: Path) -> Path:
    model = cad_cli_root / "examples" / "models" / "cube.py"
    if not model.is_file():
        pytest.skip(f"cad-cli example cube model not found at {model}")
    return model


@pytest.fixture(scope="session")
def hole_plate_model(cad_cli_root: Path) -> Path:
    model = cad_cli_root / "examples" / "models" / "hole_plate.py"
    if not model.is_file():
        pytest.skip(f"cad-cli example hole_plate model not found at {model}")
    return model


@pytest.fixture(scope="session")
def require_cad_cli() -> None:
    if shutil.which("cad") is None:
        pytest.skip("cad CLI not on PATH")


@pytest.fixture(scope="session")
def require_blender() -> None:
    import os

    if os.environ.get("CAD_BLENDER_BIN"):
        return
    if shutil.which("blender") is None:
        pytest.skip("blender not on PATH and CAD_BLENDER_BIN unset")
