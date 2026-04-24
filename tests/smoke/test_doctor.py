"""Smoke test: `formloop doctor` must pass on a healthy dev environment.

REQ: FLH-V-003, FLH-V-007
"""

from __future__ import annotations

import os
import shutil

import pytest
from typer.testing import CliRunner

from formloop.cli import app

runner = CliRunner()

pytestmark = pytest.mark.smoke


def _require_dev_env() -> None:
    missing = []
    if not os.environ.get("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY")
    if shutil.which("cad") is None:
        missing.append("cad")
    if not os.environ.get("CAD_BLENDER_BIN") and shutil.which("blender") is None:
        missing.append("blender")
    if missing:
        pytest.skip(f"doctor smoke requires: {missing}")


def test_doctor_exits_zero() -> None:
    _require_dev_env()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0, result.output
    assert "all checks passed" in result.output
