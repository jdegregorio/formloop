"""Shared helpers for the ``formloop ui`` daemon controls."""

from __future__ import annotations

import os
import socket
from pathlib import Path

from ..config.profiles import HarnessConfig


def pid_file_path(config: HarnessConfig) -> Path:
    path = Path(config.api.pid_file)
    if not path.is_absolute():
        path = config.repo_root / path
    return path


def log_file_path(config: HarnessConfig) -> Path:
    path = Path(config.api.log_file)
    if not path.is_absolute():
        path = config.repo_root / path
    return path


def is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def port_open(host: str, port: int, timeout: float = 0.3) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
            return True
        except OSError:
            return False
