"""Narrator service contract tests.

REQ: FLH-F-024, FLH-F-026, FLH-NF-010

Covers the orchestrator-facing facade: success path, fallback on failure,
fallback on timeout, and ``fallback_only`` short-circuit.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from formloop.agents.narrator import NarrationInput, NarrationOutput
from formloop.orchestrator.narrator import Narrator

pytestmark = pytest.mark.asyncio


@dataclass
class _FakeRunResult:
    final_output: NarrationOutput


def _payload() -> NarrationInput:
    return NarrationInput(
        phase="revision",
        just_completed="ran the CAD designer",
        next_step="persist and review",
        why="",
        signals={"attempt": 1},
    )


async def test_fallback_only_skips_llm() -> None:
    n = Narrator(fallback_only=True)
    text, err = await n.narrate(_payload(), fallback="planning")
    assert text == "planning"
    assert err is None


async def test_success_path_returns_narration(monkeypatch) -> None:
    n = Narrator(fallback_only=True)
    # Force the agent path on but stub Runner.run.
    n.fallback_only = False
    n._agent = object()  # Runner.run is stubbed below; agent value unused.

    async def fake_run(agent, input):  # noqa: A002
        return _FakeRunResult(final_output=NarrationOutput(text="we built the cube"))

    monkeypatch.setattr("formloop.orchestrator.narrator.Runner.run", fake_run)
    text, err = await n.narrate(_payload(), fallback="building")
    assert text == "we built the cube"
    assert err is None


async def test_exception_falls_back(monkeypatch) -> None:
    n = Narrator(fallback_only=True)
    n.fallback_only = False
    n._agent = object()

    async def boom(agent, input):  # noqa: A002
        raise RuntimeError("model offline")

    monkeypatch.setattr("formloop.orchestrator.narrator.Runner.run", boom)
    text, err = await n.narrate(_payload(), fallback="building cube")
    assert text == "building cube"
    assert err is not None
    assert "RuntimeError" in err


async def test_timeout_falls_back(monkeypatch) -> None:
    n = Narrator(fallback_only=True, timeout_seconds=0.05)
    n.fallback_only = False
    n._agent = object()

    async def slow(agent, input):  # noqa: A002
        await asyncio.sleep(1.0)
        return _FakeRunResult(final_output=NarrationOutput(text="late"))

    monkeypatch.setattr("formloop.orchestrator.narrator.Runner.run", slow)
    text, err = await n.narrate(_payload(), fallback="planning")
    assert text == "planning"
    assert err is not None
    assert "timeout" in err


async def test_empty_output_falls_back(monkeypatch) -> None:
    n = Narrator(fallback_only=True)
    n.fallback_only = False
    n._agent = object()

    async def empty(agent, input):  # noqa: A002
        return _FakeRunResult(final_output=NarrationOutput(text="   "))

    monkeypatch.setattr("formloop.orchestrator.narrator.Runner.run", empty)
    text, err = await n.narrate(_payload(), fallback="kicking off")
    assert text == "kicking off"
    assert err == "empty narration"


async def test_auto_falls_back_when_no_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    n = Narrator.auto()
    assert n.fallback_only is True
    text, err = await n.narrate(_payload(), fallback="getting started")
    assert text == "getting started"
    assert err is None
