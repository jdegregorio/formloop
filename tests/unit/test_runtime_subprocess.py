"""Unit tests for the subprocess wrapper.

REQ: FLH-V-001, FLH-D-004
"""

from __future__ import annotations

import sys

import pytest

from formloop.runtime.subprocess import CliError, run_cli


def test_runs_and_captures_stdout() -> None:
    r = run_cli([sys.executable, "-c", "print('hello')"])
    assert r.returncode == 0
    assert "hello" in r.stdout


def test_parses_json_stdout() -> None:
    r = run_cli([sys.executable, "-c", "import json; print(json.dumps({'x': 1}))"])
    assert r.parse_json() == {"x": 1}


def test_raises_on_bad_json() -> None:
    r = run_cli([sys.executable, "-c", "print('not json')"])
    with pytest.raises(CliError, match="JSON"):
        r.parse_json()


def test_raises_on_nonzero_exit() -> None:
    with pytest.raises(CliError) as excinfo:
        run_cli([sys.executable, "-c", "import sys; sys.exit(7)"])
    assert excinfo.value.returncode == 7


def test_missing_executable_becomes_cli_error() -> None:
    with pytest.raises(CliError, match="not found"):
        run_cli(["definitely-no-such-binary-1234"])


def test_does_not_raise_when_check_false() -> None:
    r = run_cli([sys.executable, "-c", "import sys; sys.exit(3)"], check=False)
    assert r.returncode == 3
