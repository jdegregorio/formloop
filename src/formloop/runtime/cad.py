from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from pydantic import BaseModel, Field

from formloop.models import ToolCallRecord


class CadBuildResult(BaseModel):
    step_path: str
    glb_path: str
    metadata_path: str


class CadRenderResult(BaseModel):
    render_sheet_path: str
    view_paths: list[str] = Field(default_factory=list)
    metadata_path: str | None = None


class CadInspectResult(BaseModel):
    measurements: dict[str, float | str]


class CadCompareResult(BaseModel):
    metrics: dict[str, float | str]
    summary: str


class CadRuntime:
    def __init__(self, cad_command: str, cwd: Path) -> None:
        self.cad_command = cad_command
        self.cwd = cwd

    def check_command(self) -> bool:
        if Path(self.cad_command).exists():
            return True
        return shutil.which(self.cad_command) is not None

    def build(self, model_source: Path, output_dir: Path) -> tuple[CadBuildResult, ToolCallRecord]:
        output_dir.mkdir(parents=True, exist_ok=True)
        command = [self.cad_command, "build", "--model-source", str(model_source), "--output-dir", str(output_dir)]
        data, record = self._run_json(command)
        return CadBuildResult.model_validate(data), record

    def render(self, glb_path: Path, output_dir: Path) -> tuple[CadRenderResult, ToolCallRecord]:
        output_dir.mkdir(parents=True, exist_ok=True)
        command = [self.cad_command, "render", "--glb-path", str(glb_path), "--output-dir", str(output_dir)]
        data, record = self._run_json(command)
        return CadRenderResult.model_validate(data), record

    def inspect(self, step_path: Path, measurements: list[str]) -> tuple[CadInspectResult, ToolCallRecord]:
        command = [
            self.cad_command,
            "inspect",
            "--step-path",
            str(step_path),
            "--measurements",
            json.dumps(measurements),
        ]
        data, record = self._run_json(command)
        return CadInspectResult.model_validate(data), record

    def compare(self, candidate_step: Path, truth_step: Path) -> tuple[CadCompareResult, ToolCallRecord]:
        command = [
            self.cad_command,
            "compare",
            "--candidate-step",
            str(candidate_step),
            "--truth-step",
            str(truth_step),
        ]
        data, record = self._run_json(command)
        return CadCompareResult.model_validate(data), record

    def _run_json(self, command: list[str]) -> tuple[dict, ToolCallRecord]:
        completed = subprocess.run(
            command,
            cwd=self.cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        record = ToolCallRecord(
            tool="cad-cli",
            command=command,
            cwd=str(self.cwd),
            returncode=completed.returncode,
            stdout_excerpt=completed.stdout[-4000:],
            stderr_excerpt=completed.stderr[-4000:],
        )
        if completed.returncode != 0:
            raise RuntimeError(f"cad command failed: {' '.join(command)}\n{completed.stderr}")
        return json.loads(completed.stdout), record

