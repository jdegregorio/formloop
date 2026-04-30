"""`formloop ui` command group."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable

import typer

from ...config.profiles import HarnessConfig
from ..ui_daemon import is_running, log_file_path, pid_file_path, port_open


def register(ui_app: typer.Typer, resolve_config: Callable[[], HarnessConfig]) -> None:
    @ui_app.command("start")
    def ui_start_cmd() -> None:
        """Launch the same-origin browser UI and polling HTTP API daemon."""

        config = resolve_config()
        pid_file = pid_file_path(config)
        log_file = log_file_path(config)

        if pid_file.is_file():
            existing = int(pid_file.read_text().strip() or "0")
            if existing and is_running(existing):
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
        deadline = time.monotonic() + 8.0
        while time.monotonic() < deadline:
            if port_open(config.api.host, config.api.port):
                typer.echo(f"started pid={proc.pid} http://{config.api.host}:{config.api.port}")
                return
            time.sleep(0.25)
        typer.echo(
            f"started pid={proc.pid} (port {config.api.port} not responding yet; see {log_file})"
        )

    @ui_app.command("stop")
    def ui_stop_cmd() -> None:
        """Stop the HTTP API daemon."""

        config = resolve_config()
        pid_file = pid_file_path(config)
        if not pid_file.is_file():
            typer.echo("not running")
            return
        pid = int(pid_file.read_text().strip() or "0")
        if pid and is_running(pid):
            os.kill(pid, signal.SIGTERM)
            typer.echo(f"sent SIGTERM to pid={pid}")
        else:
            typer.echo("stale pid file — removing")
        pid_file.unlink(missing_ok=True)

    @ui_app.command("status")
    def ui_status_cmd() -> None:
        """Report status of the HTTP API daemon."""

        config = resolve_config()
        pid_file = pid_file_path(config)
        if not pid_file.is_file():
            typer.echo("not running")
            raise typer.Exit(code=1)
        pid = int(pid_file.read_text().strip() or "0")
        alive = pid and is_running(pid)
        reachable = port_open(config.api.host, config.api.port)
        typer.echo(
            f"pid={pid} alive={alive} "
            f"url=http://{config.api.host}:{config.api.port} reachable={reachable}"
        )
        if not alive or not reachable:
            raise typer.Exit(code=1)
