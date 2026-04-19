"""Typer CLI for the Formloop harness."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Annotated

import typer
import uvicorn

from .bootstrap import bootstrap_environment
from .config import load_config
from .http.api import create_app
from .models import RunCreateRequest
from .paths import repo_root
from .services.doctor import DoctorService
from .services.evals import EvalService
from .services.harness import HarnessService

app = typer.Typer(help="Formloop operator CLI")
ui_app = typer.Typer(help="Stub UI lifecycle commands")
eval_app = typer.Typer(help="Developer eval commands")
app.add_typer(ui_app, name="ui")
app.add_typer(eval_app, name="eval")


@app.command("run")
def run_command(
    prompt: str,
    profile: Annotated[str | None, typer.Option(help="Named harness profile")] = None,
    reference_image: Annotated[
        Path | None,
        typer.Option(exists=True, dir_okay=False),
    ] = None,
) -> None:
    """Run the full harness end-to-end."""
    # Req: FLH-F-012, FLH-F-013, FLH-V-005
    bootstrap_environment()
    service = HarnessService()
    outcome = service.run_sync(
        RunCreateRequest(
            prompt=prompt,
            profile=profile,
            reference_image=str(reference_image) if reference_image else None,
        )
    )
    typer.echo(outcome.final_message)
    typer.echo(str(service.store.run_dir(outcome.run.run_name)))


@app.command("doctor")
def doctor_command() -> None:
    bootstrap_environment()
    checks = DoctorService().run_checks()
    for check in checks:
        status = "OK" if check.ok else "FAIL"
        typer.echo(f"{status:4} {check.name}: {check.detail}")
    if not all(check.ok for check in checks):
        raise typer.Exit(code=1)


@app.command("update")
def update_command() -> None:
    """Perform a safe checkout-oriented update."""
    # Req: FLH-F-013
    bootstrap_environment()
    repo = repo_root()
    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    if status.stdout.strip():
        typer.echo("Refusing update from a dirty checkout. Commit or stash changes first.")
        raise typer.Exit(code=1)
    typer.echo(
        "Clean checkout detected. Safe update path is: git pull --ff-only && uv sync --extra dev"
    )


@ui_app.command("start")
def ui_start() -> None:
    typer.echo("UI is not implemented yet in this phase. Use the HTTP API or CLI instead.")


@ui_app.command("stop")
def ui_stop() -> None:
    typer.echo("UI is not implemented yet in this phase. Nothing to stop.")


@ui_app.command("status")
def ui_status() -> None:
    typer.echo("UI is not implemented yet in this phase. Backend harness remains available.")


@eval_app.command("run")
def eval_run(dataset_path: str, profile: str = typer.Option("normal")) -> None:
    bootstrap_environment()
    report = EvalService().run_dataset_sync(dataset_path, profile=profile)
    typer.echo(report.model_dump_json(indent=2))


@eval_app.command("report")
def eval_report(which: str = typer.Argument("latest")) -> None:
    bootstrap_environment()
    if which != "latest":
        raise typer.BadParameter("Only 'latest' is supported right now.")
    report = EvalService().load_latest_report()
    typer.echo(report.model_dump_json(indent=2))


@app.command("serve")
def serve_command() -> None:
    """Run the HTTP API locally."""
    bootstrap_environment()
    config = load_config()
    uvicorn.run(
        create_app(),
        host=config.runtime.http_host,
        port=config.runtime.http_port,
    )


def main() -> None:
    bootstrap_environment()
    app()


if __name__ == "__main__":
    main()
