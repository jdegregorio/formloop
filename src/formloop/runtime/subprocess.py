"""Thin subprocess wrapper used by every external-tool invocation.

REQ: FLH-D-004, FLH-D-020
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class CliError(RuntimeError):
    """Raised when an external CLI exits non-zero or returns malformed JSON."""

    def __init__(
        self,
        *,
        cmd: list[str],
        returncode: int,
        stdout: str,
        stderr: str,
        message: str | None = None,
    ) -> None:
        super().__init__(
            message
            or f"{cmd[0]} exited with code {returncode}: {stderr.strip() or stdout.strip()!r}"
        )
        self.cmd = cmd
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@dataclass(frozen=True, slots=True)
class CliResult:
    cmd: list[str]
    returncode: int
    stdout: str
    stderr: str

    def parse_json(self) -> Any:
        try:
            return json.loads(self.stdout)
        except json.JSONDecodeError as exc:
            raise CliError(
                cmd=self.cmd,
                returncode=self.returncode,
                stdout=self.stdout,
                stderr=self.stderr,
                message=f"expected JSON on stdout but got: {exc}",
            ) from exc


def run_cli(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout: float | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> CliResult:
    """Run ``cmd`` as a subprocess, capture stdout/stderr, return CliResult.

    Raises :class:`CliError` on non-zero exit when ``check`` is True.
    """

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd is not None else None,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise CliError(
            cmd=cmd,
            returncode=127,
            stdout="",
            stderr=str(exc),
            message=f"executable not found: {cmd[0]}",
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise CliError(
            cmd=cmd,
            returncode=-1,
            stdout=exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or ""),
            stderr=exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or ""),
            message=f"{cmd[0]} timed out after {timeout}s",
        ) from exc

    result = CliResult(
        cmd=cmd,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )
    if check and result.returncode != 0:
        raise CliError(
            cmd=cmd,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    return result
