"""Typer-based operator CLI.

REQ: FLH-F-012, FLH-F-013, FLH-F-027, FLH-D-015, FLH-D-016, FLH-V-007
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated

import typer

from ..config.env import load_env_local, repo_root
from ..config.profiles import HarnessConfig, load_config
from ..orchestrator import drive_run
from ..runtime.cad_cli import locate_blender, locate_cad
from .run_renderer import make_renderer
from .run_report import print_run_footer, print_run_header


app = typer.Typer(
    name="formloop",
    help="Formloop harness operator CLI.",
    no_args_is_help=True,
    add_completion=False,
)


eval_app = typer.Typer(help="Eval batch runner / reporting.")
ui_app = typer.Typer(help="Manage the polling HTTP API daemon.")

app.add_typer(eval_app, name="eval")
app.add_typer(ui_app, name="ui")


# ---------------------------------------------------------------------------
# formloop run
# ---------------------------------------------------------------------------


def _resolve_config() -> HarnessConfig:
    load_env_local()
    return load_config()


@app.command("run")
def run_cmd(
    prompt: Annotated[str, typer.Argument(help="Natural-language design request.")],
    profile: Annotated[
        str | None,
        typer.Option("--profile", help="Profile name from formloop.harness.toml."),
    ] = None,
    reference_image: Annotated[
        Path | None,
        typer.Option("--reference-image", help="Optional reference image path."),
    ] = None,
    max_revisions: Annotated[
        int | None,
        typer.Option("--max-revisions", help="Override max revision attempts."),
    ] = None,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress live narration; only show the final result.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show every event with its data payload (debugging).",
        ),
    ] = False,
    no_color: Annotated[
        bool,
        typer.Option(
            "--no-color", help="Disable ANSI colors / in-place narration rewrite."
        ),
    ] = False,
) -> None:
    """Run the harness end-to-end for a single prompt (FLH-F-012, FLH-F-027).

    Live narration mirrors the UI's reasoning-trace pattern: the latest
    LLM-written status update is rewritten in place between scrolling
    history. Use ``--verbose`` for the full event stream, ``--quiet`` to
    suppress narration entirely.
    """

    config = _resolve_config()
    ref = str(reference_image.resolve()) if reference_image else None
    resolved_profile = config.profile(profile)

    renderer = make_renderer(quiet=quiet, verbose=verbose, color=not no_color)

    if not quiet:
        print_run_header(
            prompt=prompt,
            profile_name=resolved_profile.name,
            model=resolved_profile.model,
            reference_image=ref,
            color=not no_color,
        )

    result = asyncio.run(
        drive_run(
            prompt,
            config=config,
            profile=profile,
            reference_image=ref,
            max_revisions=max_revisions,
            event_hook=renderer,
        )
    )
    renderer.finalize()

    if not quiet:
        print_run_footer(
            run_name=result["run_name"],
            status=result["status"],
            delivered_revision=result.get("delivered_revision"),
            artifacts_dir=(
                config.runs_dir / result["run_name"] / "revisions" / result["delivered_revision"]
                if result.get("delivered_revision")
                else None
            ),
            final_answer=result.get("final_answer"),
            color=not no_color,
        )

    if result["status"] != "succeeded":
        raise typer.Exit(code=2)


# ---------------------------------------------------------------------------
# formloop doctor
# ---------------------------------------------------------------------------


@app.command("doctor")
def doctor_cmd() -> None:
    """Verify the environment is ready to run the harness (FLH-V-007)."""

    load_env_local()
    problems: list[str] = []

    py = sys.version_info
    if py < (3, 11):
        problems.append(
            f"Python 3.11+ required; detected {py.major}.{py.minor}.{py.micro}"
        )
    typer.echo(f"python:   {py.major}.{py.minor}.{py.micro}")

    cad = locate_cad()
    typer.echo(f"cad:      {cad}")
    if cad is None:
        problems.append("`cad` CLI not found on PATH — install cad-cli editable")

    try:
        blender = locate_blender()
        typer.echo(f"blender:  {blender}")
    except Exception as exc:
        typer.echo(f"blender:  NOT FOUND ({exc})")
        problems.append(str(exc))

    if not os.environ.get("OPENAI_API_KEY"):
        problems.append("OPENAI_API_KEY not set (check .env.local)")
        typer.echo("openai:   NO KEY")
    else:
        typer.echo("openai:   OPENAI_API_KEY present")

    # Real end-to-end cad-cli conformance: a tiny build on the example cube.
    if cad is not None:
        try:
            from ..runtime.cad_cli import cad_build

            cube_model = repo_root().parent / "cad-cli" / "examples" / "models" / "cube.py"
            if cube_model.is_file():
                out = repo_root() / "var" / ".doctor" / "build"
                if out.exists():
                    shutil.rmtree(out)
                build = cad_build(
                    model_path=cube_model, output_dir=out, overrides={"size": 5}
                )
                typer.echo(
                    f"cad build: ok  volume={build.volume:.1f}mm³ "
                    f"bbox={build.bounding_box.size}"
                )
            else:
                typer.echo(f"cad build: skipped (no cube example at {cube_model})")
        except Exception as exc:  # noqa: BLE001 -- diagnostic output
            problems.append(f"cad build smoke failed: {exc}")
            typer.echo(f"cad build: FAILED — {exc}")

    if problems:
        typer.echo("")
        for p in problems:
            typer.echo(f"✗ {p}", err=True)
        raise typer.Exit(code=1)
    typer.echo("")
    typer.echo("all checks passed.")


# ---------------------------------------------------------------------------
# formloop update
# ---------------------------------------------------------------------------


@app.command("update")
def update_cmd() -> None:
    """Report current formloop version and offer an update command hint."""

    try:
        ver = version("formloop")
    except PackageNotFoundError:
        ver = "unknown (not installed via pip/uv)"
    typer.echo(f"formloop: {ver}")
    typer.echo("To upgrade inside this worktree: `uv sync`")


# ---------------------------------------------------------------------------
# formloop eval
# ---------------------------------------------------------------------------


@eval_app.command("run")
def eval_run_cmd(
    dataset_path: Annotated[Path, typer.Argument(help="Path to cases.jsonl.")],
    profile: Annotated[str | None, typer.Option("--profile")] = None,
    batch_name: Annotated[str | None, typer.Option("--batch-name")] = None,
    max_revisions: Annotated[int | None, typer.Option("--max-revisions")] = None,
) -> None:
    """Run an eval batch (FLH-F-014, FLH-D-018)."""

    from ..evals.runner import run_eval_batch

    config = _resolve_config()
    asyncio.run(
        run_eval_batch(
            dataset_path=dataset_path,
            config=config,
            profile=profile,
            batch_name=batch_name,
            max_revisions=max_revisions,
        )
    )


@eval_app.command("report")
def eval_report_cmd(
    batch: Annotated[str, typer.Argument(help="Batch name or 'latest'.")] = "latest",
) -> None:
    """Render aggregated eval report for a batch."""

    from ..evals.report import render_report

    config = _resolve_config()
    path = render_report(config, batch)
    typer.echo(f"report: {path}")


# ---------------------------------------------------------------------------
# formloop ui start|stop|status
# ---------------------------------------------------------------------------


def _pid_file_path(config: HarnessConfig) -> Path:
    path = Path(config.api.pid_file)
    if not path.is_absolute():
        path = config.repo_root / path
    return path


def _log_file_path(config: HarnessConfig) -> Path:
    path = Path(config.api.log_file)
    if not path.is_absolute():
        path = config.repo_root / path
    return path


def _is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _port_open(host: str, port: int, timeout: float = 0.3) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
            return True
        except OSError:
            return False


@ui_app.command("start")
def ui_start_cmd() -> None:
    """Launch the polling HTTP API as a detached daemon."""

    config = _resolve_config()
    pid_file = _pid_file_path(config)
    log_file = _log_file_path(config)

    if pid_file.is_file():
        existing = int(pid_file.read_text().strip() or "0")
        if existing and _is_running(existing):
            typer.echo(f"already running (pid={existing})")
            raise typer.Exit(code=0)
        pid_file.unlink(missing_ok=True)

    pid_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_fh = log_file.open("ab")
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "formloop.api.app:app",
        "--host",
        config.api.host,
        "--port",
        str(config.api.port),
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=log_fh,
        stderr=log_fh,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        cwd=config.repo_root,
    )
    pid_file.write_text(str(proc.pid))
    # wait briefly for the port to open
    deadline = time.monotonic() + 8.0
    while time.monotonic() < deadline:
        if _port_open(config.api.host, config.api.port):
            typer.echo(
                f"started pid={proc.pid} http://{config.api.host}:{config.api.port}"
            )
            return
        time.sleep(0.25)
    typer.echo(
        f"started pid={proc.pid} (port {config.api.port} not responding yet; see {log_file})"
    )


@ui_app.command("stop")
def ui_stop_cmd() -> None:
    """Stop the HTTP API daemon."""

    config = _resolve_config()
    pid_file = _pid_file_path(config)
    if not pid_file.is_file():
        typer.echo("not running")
        return
    pid = int(pid_file.read_text().strip() or "0")
    if pid and _is_running(pid):
        os.kill(pid, signal.SIGTERM)
        typer.echo(f"sent SIGTERM to pid={pid}")
    else:
        typer.echo("stale pid file — removing")
    pid_file.unlink(missing_ok=True)


@ui_app.command("status")
def ui_status_cmd() -> None:
    """Report status of the HTTP API daemon."""

    config = _resolve_config()
    pid_file = _pid_file_path(config)
    if not pid_file.is_file():
        typer.echo("not running")
        raise typer.Exit(code=1)
    pid = int(pid_file.read_text().strip() or "0")
    alive = pid and _is_running(pid)
    reachable = _port_open(config.api.host, config.api.port)
    typer.echo(
        f"pid={pid} alive={alive} "
        f"url=http://{config.api.host}:{config.api.port} reachable={reachable}"
    )
    if not alive or not reachable:
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# formloop snapshot <run-name>  (helper for humans/tests)
# ---------------------------------------------------------------------------


@app.command("snapshot")
def snapshot_cmd(run_name: str) -> None:
    """Print the snapshot.json for a run."""

    config = _resolve_config()
    path = config.runs_dir / run_name / "snapshot.json"
    if not path.is_file():
        typer.echo(f"no snapshot at {path}", err=True)
        raise typer.Exit(code=1)
    typer.echo(json.dumps(json.loads(path.read_text()), indent=2))
