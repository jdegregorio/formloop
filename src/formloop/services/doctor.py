"""Operator health checks."""

from __future__ import annotations

import os
import shutil

from ..config import HarnessConfig, load_config
from ..models import DoctorCheck
from ..runtime.cad import CadCliRuntime


class DoctorService:
    # Req: FLH-F-013, FLH-V-007
    def __init__(
        self,
        *,
        config: HarnessConfig | None = None,
        cad_runtime: CadCliRuntime | None = None,
    ) -> None:
        self.config = config or load_config()
        self.cad_runtime = cad_runtime or CadCliRuntime()

    def run_checks(self) -> list[DoctorCheck]:
        checks: list[DoctorCheck] = []

        checks.append(
            DoctorCheck(
                name="config",
                ok=True,
                detail=f"default profile={self.config.runtime.default_profile}",
            )
        )
        checks.append(
            DoctorCheck(
                name="openai_api_key",
                ok=bool(os.environ.get("OPENAI_API_KEY")),
                detail="present" if os.environ.get("OPENAI_API_KEY") else "missing OPENAI_API_KEY",
            )
        )
        checks.append(
            DoctorCheck(
                name="blender",
                ok=bool(shutil.which("blender")),
                detail=shutil.which("blender") or "blender not found on PATH",
            )
        )
        run_root = self.config.run_root_path()
        run_root.mkdir(parents=True, exist_ok=True)
        writable_probe = run_root / ".doctor-write-check"
        try:
            writable_probe.write_text("ok", encoding="utf-8")
            writable_probe.unlink()
            checks.append(DoctorCheck(name="runtime_root", ok=True, detail=str(run_root)))
        except OSError as exc:
            checks.append(DoctorCheck(name="runtime_root", ok=False, detail=str(exc)))

        try:
            smoke = self.cad_runtime.doctor_smoke()
            build_keys = sorted(smoke["build"].keys())
            inspect_keys = sorted(smoke["inspect"].keys())
            ok = "schema_version" in build_keys and "data" in inspect_keys
            checks.append(
                DoctorCheck(
                    name="cad_cli_contract",
                    ok=ok,
                    detail=f"build_keys={build_keys}; inspect_keys={inspect_keys}",
                )
            )
        except Exception as exc:  # pragma: no cover - integration/doctor path
            checks.append(DoctorCheck(name="cad_cli_contract", ok=False, detail=str(exc)))
        return checks
