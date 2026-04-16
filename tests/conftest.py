from __future__ import annotations

from pathlib import Path

import pytest

from formloop.service import create_service


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def fake_cad_path(repo_root: Path) -> str:
    return str((repo_root / "scripts" / "fake_cad").resolve())


@pytest.fixture
def configured_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fake_cad_path: str, repo_root: Path) -> Path:
    monkeypatch.chdir(repo_root)
    monkeypatch.setenv("FORMLOOP_LLM_BACKEND", "heuristic")
    monkeypatch.setenv("FORMLOOP_CAD_COMMAND", fake_cad_path)
    monkeypatch.setenv("FORMLOOP_RUN_STORE", str(tmp_path / ".formloop-test"))
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    return repo_root


@pytest.fixture
def service(configured_env: Path):
    return create_service(configured_env)

