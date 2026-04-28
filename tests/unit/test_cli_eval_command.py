from __future__ import annotations

from typer.testing import CliRunner

from formloop.cli import app

runner = CliRunner()


def test_eval_run_command_passes_worker_and_reference_flags(monkeypatch) -> None:
    captured = {}

    async def fake_run_eval_batch(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("formloop.evals.runner.run_eval_batch", fake_run_eval_batch)

    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "datasets/basic_shapes",
            "--workers",
            "3",
            "--no-reference-images",
        ],
    )

    assert result.exit_code == 0
    assert captured["workers"] == 3
    assert captured["reference_images_enabled"] is False


def test_eval_run_command_defaults_to_five_workers(monkeypatch) -> None:
    captured = {}

    async def fake_run_eval_batch(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("formloop.evals.runner.run_eval_batch", fake_run_eval_batch)

    result = runner.invoke(app, ["eval", "run", "datasets/basic_shapes"])

    assert result.exit_code == 0
    assert captured["workers"] == 5
    assert captured["reference_images_enabled"] is True
