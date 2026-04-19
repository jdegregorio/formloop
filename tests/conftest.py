from __future__ import annotations

from pathlib import Path

import pytest

from formloop.config import load_config
from formloop.paths import repo_root


@pytest.fixture
def formloop_root() -> Path:
    return repo_root()


@pytest.fixture
def test_config(tmp_path: Path):
    config = load_config().model_copy(deep=True)
    config.runtime.run_root = str(tmp_path / "runs")
    return config
