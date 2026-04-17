from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from formloop.cli import app
from formloop.models import ArtifactRecord, EffectiveRuntime, ReviewSummary, RunRecord
from formloop.types import ArtifactKind, ReviewDecision, RunStatus


class DummyService:
    def __init__(self, report_path: Path | None = None) -> None:
        self.report_path = report_path
        self.runs: dict[str, RunRecord] = {}

    def execute_run(self, request):
        run = RunRecord(
            prompt=request.prompt,
            status=RunStatus.SUCCEEDED,
            effective_runtime=EffectiveRuntime(
                profile=request.profile or "normal",
                provider="openai_responses",
                model="gpt-5.4",
                thinking="high",
                backend="heuristic",
            ),
            latest_review_summary=ReviewSummary(
                decision=ReviewDecision.PASS,
                confidence=0.9,
                key_findings=["ok"],
            ),
            final_artifacts=[ArtifactRecord(kind=ArtifactKind.STEP, path="revisions/0/model.step", revision=0, label="step")],
        )
        self.runs[run.run_id] = run
        return run

    def doctor(self, profiles=None):
        return {"ok": True, "cad_command": "cad", "issues": [], "profiles": profiles or ["normal"]}

    def execute_eval(self, dataset, profile_name=None):
        return SimpleNamespace(
            dataset=dataset,
            aggregate_metrics={"case_count": 1, "passed": 1, "failed": 0},
            report_path="report.md",
            model_dump_json=lambda indent=2: json.dumps({"dataset": dataset, "aggregate_metrics": {"case_count": 1}}, indent=indent),
        )

    def latest_eval_report(self, dataset):
        assert self.report_path is not None
        return self.report_path


def test_cli_run_and_doctor(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    service = DummyService()
    monkeypatch.setattr("formloop.cli.create_service", lambda: service)

    result = runner.invoke(app, ["run", "Create a block", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["status"] == "succeeded"

    doctor = runner.invoke(app, ["doctor", "--json"])
    assert doctor.exit_code == 0
    assert json.loads(doctor.stdout)["ok"] is True


def test_cli_eval_and_report(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = CliRunner()
    report_path = tmp_path / "latest.md"
    report_path.write_text("# Report", encoding="utf-8")
    service = DummyService(report_path=report_path)
    monkeypatch.setattr("formloop.cli.create_service", lambda: service)

    eval_run = runner.invoke(app, ["eval", "run", "basic_shapes", "--json"])
    assert eval_run.exit_code == 0
    assert json.loads(eval_run.stdout)["aggregate_metrics"]["case_count"] == 1

    report = runner.invoke(app, ["eval", "report", "basic_shapes"])
    assert report.exit_code == 0
    assert "# Report" in report.stdout


def test_cli_run_reports_failure_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()

    class FailingService(DummyService):
        def execute_run(self, request):
            raise RuntimeError("backend exploded")

    monkeypatch.setattr("formloop.cli.create_service", lambda: FailingService())

    result = runner.invoke(app, ["run", "Create a block"])
    assert result.exit_code == 1
    assert "Run failed: backend exploded" in result.stdout


def test_cli_ui_lifecycle(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = CliRunner()
    state_root = tmp_path / ".formloop"
    config = SimpleNamespace(
        app=SimpleNamespace(
            api_host="127.0.0.1",
            api_port=8040,
            ui_server_import="formloop.api.app:create_app",
        ),
        run_store_path=state_root,
        project_root=tmp_path,
    )
    monkeypatch.setattr("formloop.cli.load_config", lambda: config)

    class FakePopen:
        pid = 43210

    monkeypatch.setattr("formloop.cli.subprocess.Popen", lambda *args, **kwargs: FakePopen())
    killed: list[int] = []
    monkeypatch.setattr("formloop.cli.os.kill", lambda pid, sig=0: killed.append(pid))

    started = runner.invoke(app, ["ui", "start"])
    assert started.exit_code == 0
    assert "Started harness API server" in started.stdout

    status = runner.invoke(app, ["ui", "status"])
    assert status.exit_code == 0
    assert "running pid=43210" in status.stdout

    stopped = runner.invoke(app, ["ui", "stop"])
    assert stopped.exit_code == 0
    assert "Stopped harness API server." in stopped.stdout
    assert killed
