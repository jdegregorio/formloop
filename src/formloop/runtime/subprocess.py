"""Thin subprocess wrapper used by every external-tool invocation.

REQ: FLH-D-004, FLH-D-020
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CliError(RuntimeError):
    """Raised when an external CLI exits non-zero or returns malformed JSON.

    When the underlying tool emits a structured error payload (cad-cli v0.1.2+
    writes ``{"error": {"type", "message", "traceback", "cause", "exit_code"}}``
    on stderr under ``--format json``), the parsed fields are captured on
    :attr:`error_type`, :attr:`error_message`, :attr:`traceback_str`, and
    :attr:`cause`. Callers can use these to surface a real traceback to the
    designer instead of string-scraping stderr.
    """

    def __init__(
        self,
        *,
        cmd: list[str],
        returncode: int,
        stdout: str,
        stderr: str,
        message: str | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
        traceback_str: str | None = None,
        cause: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            message
            or f"{cmd[0]} exited with code {returncode}: {stderr.strip() or stdout.strip()!r}"
        )
        self.cmd = cmd
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.error_type = error_type
        self.error_message = error_message
        self.traceback_str = traceback_str
        self.cause = cause


def _parse_cad_error_payload(stderr: str) -> dict[str, Any] | None:
    """Best-effort: extract cad-cli's structured ``{"error": {...}}`` payload.

    Returns the inner ``error`` dict if recognized, else ``None``.
    """

    text = (stderr or "").strip()
    if not text:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        # cad-cli prints the JSON on a single block; tolerate trailing junk.
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            payload = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    if not isinstance(payload, dict):
        return None
    err = payload.get("error")
    if not isinstance(err, dict):
        return None
    return err


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

    logger.debug("exec: %s cwd=%s timeout=%s", cmd, cwd, timeout)
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
        logger.warning("exec not found: %s", cmd[0])
        raise CliError(
            cmd=cmd,
            returncode=127,
            stdout="",
            stderr=str(exc),
            message=f"executable not found: {cmd[0]}",
        ) from exc
    except subprocess.TimeoutExpired as exc:
        logger.warning("exec timeout: %s after %ss", cmd[0], timeout)
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
    logger.debug(
        "exit: %s rc=%d stdout=%dB stderr=%dB",
        cmd[0],
        result.returncode,
        len(result.stdout),
        len(result.stderr),
    )
    if check and result.returncode != 0:
        logger.warning(
            "cli error: %s rc=%d stderr=%r",
            cmd[0],
            result.returncode,
            result.stderr[:200],
        )
        err = _parse_cad_error_payload(result.stderr)
        if err is not None:
            cause_raw = err.get("cause")
            cause: dict[str, str] | None = None
            if isinstance(cause_raw, dict):
                cause = {
                    "type": str(cause_raw.get("type") or ""),
                    "message": str(cause_raw.get("message") or ""),
                }
            raise CliError(
                cmd=cmd,
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                message=str(err.get("message") or "")
                or f"{cmd[0]} exited with code {result.returncode}",
                error_type=str(err.get("type") or "") or None,
                error_message=str(err.get("message") or "") or None,
                traceback_str=(str(err["traceback"]) if err.get("traceback") else None),
                cause=cause,
            )
        raise CliError(
            cmd=cmd,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    return result
