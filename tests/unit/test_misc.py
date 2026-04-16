from __future__ import annotations

from pathlib import Path

import pytest

from formloop.agents.skills import load_builtin_skill_texts
from formloop.datasets import load_eval_cases


def test_load_builtin_skill_texts_returns_known_skill(repo_root: Path) -> None:
    skills = load_builtin_skill_texts(repo_root / "src" / "formloop" / "builtin_skills")
    assert "build123d_modeling" in skills


def test_load_eval_cases_raises_for_missing_dataset(repo_root: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_eval_cases(repo_root / "datasets", "missing_dataset")

