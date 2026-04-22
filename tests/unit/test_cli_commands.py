"""CLI command behavior for interruption and cancellation handling."""

from __future__ import annotations

from pathlib import Path

import pytest
import typer

from formloop.cli import commands
from formloop.config.profiles import ApiConfig, HarnessConfig, Profile, Timeouts
from formloop.store import RunStore


def _stub_config(tmp_path: Path) -> HarnessConfig:
    return HarnessConfig(
        default_profile="dev_test",
        max_revisions=3,
        runs_dir=tmp_path / "runs",
        evals_dir=tmp_path / "evals",
        timeouts=Timeouts(
            cad_build=60, cad_render=60, cad_inspect=60, cad_compare=60, agent_run=60
        ),
        profiles={
            "dev_test": Profile(name="dev_test", model="stub", reasoning="low"),
        },
        api=ApiConfig(host="127.0.0.1", port=0, pid_file="x.pid", log_file="x.log"),
        repo_root=tmp_path,
    )


def test_run_cmd_marks_run_cancelled_on_keyboard_interrupt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _stub_config(tmp_path)

    async def fake_continue_run(
        self, *, run, run_ctx, profile, max_revisions, user_prompt  # noqa: ARG001
    ):
        raise KeyboardInterrupt()

    monkeypatch.setattr(commands, "_resolve_config", lambda: config)
    monkeypatch.setattr(commands.RunDriver, "continue_run", fake_continue_run)

    with pytest.raises(typer.Exit) as excinfo:
        commands.run_cmd("a 20mm cube", quiet=True, no_color=True)

    assert excinfo.value.exit_code == 130

    store = RunStore(config.runs_dir)
    run = store.load_run("run-0001")
    assert run.status.value == "cancelled"
    assert run.status_detail == "run cancelled by operator"

    events = store.read_events("run-0001")
    assert events[-1].kind.value == "run_failed"
    assert events[-1].message == "run cancelled by operator"
    assert events[-1].data["error_type"] == "KeyboardInterrupt"
