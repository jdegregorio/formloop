from __future__ import annotations

import json
import os
import subprocess
import sys


def run_cli(args: list[str], env: dict[str, str], cwd: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "formloop", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_doctor_and_run(configured_env, fake_cad_path, repo_root) -> None:
    env = {
        **os.environ,
        "FORMLOOP_LLM_BACKEND": "heuristic",
        "FORMLOOP_CAD_COMMAND": fake_cad_path,
        "FORMLOOP_RUN_STORE": str(repo_root / ".formloop-smoke"),
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
    }
    doctor = run_cli(["doctor", "--json"], env, str(repo_root))
    assert doctor.returncode == 0
    assert json.loads(doctor.stdout)["ok"] is True
    run = run_cli(["run", "Create a block width 40 height 20 depth 10 for a mounting spacer.", "--json"], env, str(repo_root))
    assert run.returncode == 0
    assert json.loads(run.stdout)["status"] == "succeeded"


def test_cli_eval_and_uat(configured_env, fake_cad_path, repo_root) -> None:
    env = {
        **os.environ,
        "FORMLOOP_LLM_BACKEND": "heuristic",
        "FORMLOOP_CAD_COMMAND": fake_cad_path,
        "FORMLOOP_RUN_STORE": str(repo_root / ".formloop-smoke-2"),
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
    }
    eval_run = run_cli(["eval", "run", "basic_shapes", "--json"], env, str(repo_root))
    assert eval_run.returncode == 0
    assert json.loads(eval_run.stdout)["aggregate_metrics"]["case_count"] == 1
    uat_run = run_cli(["uat", "run", "--cad-command", fake_cad_path], env, str(repo_root))
    assert uat_run.returncode == 0
    assert "UAT report:" in uat_run.stdout
