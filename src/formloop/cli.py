from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import typer

from formloop.config import load_config
from formloop.models import DesignRequest, ReferenceImage
from formloop.service import create_service
from formloop.uat import run_uat

app = typer.Typer(help="Formloop harness operator CLI")
ui_app = typer.Typer(help="Manage the harness API server")
eval_app = typer.Typer(help="Run and inspect evals")
uat_app = typer.Typer(help="Run user-acceptance tests")
app.add_typer(ui_app, name="ui")
app.add_typer(eval_app, name="eval")
app.add_typer(uat_app, name="uat")


def _apply_overrides(backend: str | None, cad_command: str | None) -> None:
    if backend:
        os.environ["FORMLOOP_LLM_BACKEND"] = backend
    if cad_command:
        os.environ["FORMLOOP_CAD_COMMAND"] = cad_command


@app.command()
def run(
    prompt: str,
    profile: str | None = typer.Option(None, help="Named run profile."),
    reference_image: Path | None = typer.Option(None, help="Optional reference image."),
    backend: str | None = typer.Option(None, help="Override LLM backend."),
    cad_command: str | None = typer.Option(None, help="Override cad command."),
    json_output: bool = typer.Option(False, "--json", help="Emit full JSON output."),
) -> None:
    _apply_overrides(backend, cad_command)
    service = create_service()
    request = DesignRequest(
        prompt=prompt,
        profile=profile,
        reference_image=ReferenceImage(path=str(reference_image), label="cli-reference") if reference_image else None,
    )
    try:
        record = service.execute_run(request)
    except Exception as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            typer.echo(f"Run failed: {exc}")
        raise typer.Exit(1) from exc
    if json_output:
        typer.echo(record.model_dump_json(indent=2))
        return
    typer.echo(f"Run ID: {record.run_id}")
    typer.echo(f"Status: {record.status.value}")
    typer.echo(f"Profile: {record.effective_runtime.profile}")
    if record.latest_review_summary:
        typer.echo(f"Review decision: {record.latest_review_summary.decision.value}")
        typer.echo(f"Findings: {'; '.join(record.latest_review_summary.key_findings)}")
    if record.clarifications:
        typer.echo("Clarifications:")
        for question in record.clarifications[0].questions:
            typer.echo(f"- {question}")


@app.command()
def doctor(
    profile: list[str] = typer.Option(None, help="Profiles to validate."),
    backend: str | None = typer.Option(None, help="Override LLM backend."),
    cad_command: str | None = typer.Option(None, help="Override cad command."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON diagnostics."),
) -> None:
    _apply_overrides(backend, cad_command)
    service = create_service()
    result = service.doctor(profile or None)
    if json_output:
        typer.echo(json.dumps(result, indent=2))
    else:
        typer.echo(f"OK: {result['ok']}")
        typer.echo(f"cad command: {result['cad_command']}")
        for issue in result["issues"]:
            typer.echo(f"- {issue}")
    raise typer.Exit(0 if result["ok"] else 1)


@app.command()
def update() -> None:
    typer.echo("Manual update flow not implemented yet. Pull the latest repo state and re-run `uv sync`.")


@ui_app.command("start")
def ui_start(
    backend: str | None = typer.Option(None, help="Override LLM backend."),
    cad_command: str | None = typer.Option(None, help="Override cad command."),
) -> None:
    _apply_overrides(backend, cad_command)
    config = load_config()
    state_dir = config.run_store_path / "server"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "ui_server.json"
    if state_file.exists():
        typer.echo("Server already started.")
        raise typer.Exit(1)
    env = os.environ.copy()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            config.app.ui_server_import,
            "--factory",
            "--host",
            config.app.api_host,
            "--port",
            str(config.app.api_port),
        ],
        cwd=config.project_root,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    state_file.write_text(
        json.dumps({"pid": process.pid, "host": config.app.api_host, "port": config.app.api_port}, indent=2),
        encoding="utf-8",
    )
    typer.echo(f"Started harness API server on http://{config.app.api_host}:{config.app.api_port}")


@ui_app.command("status")
def ui_status() -> None:
    config = load_config()
    state_file = config.run_store_path / "server" / "ui_server.json"
    if not state_file.exists():
        typer.echo("stopped")
        return
    payload = json.loads(state_file.read_text(encoding="utf-8"))
    pid = payload["pid"]
    try:
        os.kill(pid, 0)
    except OSError:
        typer.echo("stale")
    else:
        typer.echo(f"running pid={pid} http://{payload['host']}:{payload['port']}")


@ui_app.command("stop")
def ui_stop() -> None:
    config = load_config()
    state_file = config.run_store_path / "server" / "ui_server.json"
    if not state_file.exists():
        typer.echo("Server is not running.")
        return
    payload = json.loads(state_file.read_text(encoding="utf-8"))
    os.kill(payload["pid"], signal.SIGTERM)
    state_file.unlink(missing_ok=True)
    typer.echo("Stopped harness API server.")


@eval_app.command("run")
def eval_run(
    dataset: str,
    profile: str | None = typer.Option(None, help="Eval profile."),
    backend: str | None = typer.Option(None, help="Override LLM backend."),
    cad_command: str | None = typer.Option(None, help="Override cad command."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    _apply_overrides(backend, cad_command)
    service = create_service()
    batch = service.execute_eval(dataset, profile_name=profile)
    if json_output:
        typer.echo(batch.model_dump_json(indent=2))
        return
    typer.echo(f"Dataset: {batch.dataset}")
    typer.echo(f"Passed: {batch.aggregate_metrics['passed']}")
    typer.echo(f"Failed: {batch.aggregate_metrics['failed']}")
    typer.echo(f"Report: {batch.report_path}")


@eval_app.command("report")
def eval_report_latest(dataset: str) -> None:
    service = create_service()
    report = service.latest_eval_report(dataset)
    if not report.exists():
        raise typer.Exit(f"No report found for dataset {dataset}")
    typer.echo(report.read_text(encoding="utf-8"))


@uat_app.command("run")
def uat_run(
    backend: str = typer.Option("heuristic", help="LLM backend to use for UAT."),
    cad_command: str | None = typer.Option(None, help="Override cad command."),
) -> None:
    _apply_overrides(backend, cad_command)
    service = create_service()
    report_path = run_uat(service, service.config.run_store_path / "uat")
    typer.echo(f"UAT report: {report_path}")
