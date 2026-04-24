"""Unit tests for the ``formloop run`` command boundary.

REQ: FLH-F-012, FLH-F-027
"""

from __future__ import annotations

from typer.testing import CliRunner

from formloop.cli import app

runner = CliRunner()


def test_run_command_reports_runtime_error_without_traceback(monkeypatch) -> None:
    async def fake_drive_run(*args, **kwargs):
        raise RuntimeError("missing test credential")

    monkeypatch.setattr("formloop.cli.commands.run.require_openai_key", lambda: "test-key")
    monkeypatch.setattr("formloop.cli.commands.run.drive_run", fake_drive_run)

    result = runner.invoke(app, ["run", "a 20mm cube", "--no-color"])

    assert result.exit_code == 2
    assert "formloop run failed: RuntimeError: missing test credential" in result.output
    assert "Traceback" not in result.output


def test_run_command_preflights_openai_key_without_traceback(monkeypatch) -> None:
    def missing_key():
        raise RuntimeError("OPENAI_API_KEY is not set")

    monkeypatch.setattr("formloop.cli.commands.run.require_openai_key", missing_key)

    result = runner.invoke(app, ["run", "a 20mm cube", "--no-color"])

    assert result.exit_code == 2
    assert "formloop run failed: OPENAI_API_KEY is not set" in result.output
    assert "Traceback" not in result.output
