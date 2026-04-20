"""Regenerate JSON Schema files under schemas/ from the Pydantic mirrors.

REQ: FLH-D-021, FLH-D-022

Usage:
    uv run python scripts/sync_schemas.py [--check]

Without --check the script writes schemas/<name>.schema.json files. With
--check it exits non-zero if any checked-in file is out of date, letting
CI enforce that the Pydantic models and JSON Schemas never drift.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from formloop.schemas import (
    ArtifactManifest,
    DeterministicMetrics,
    JudgeOutput,
    ProgressEvent,
    ReviewSummary,
    Revision,
    Run,
    RunCreateRequest,
    RunCreateResponse,
    RunSnapshot,
)

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"

MODEL_MAP = {
    "run": Run,
    "revision": Revision,
    "artifact-manifest": ArtifactManifest,
    "review-summary": ReviewSummary,
    "run-snapshot": RunSnapshot,
    "progress-event": ProgressEvent,
    "deterministic-metrics-output": DeterministicMetrics,
    "judge-output": JudgeOutput,
    "run-create-request": RunCreateRequest,
    "run-create-response": RunCreateResponse,
}


def render(name: str, model: type) -> str:
    schema = model.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"formloop/{name}"
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if any file differs")
    args = parser.parse_args()

    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
    drift: list[str] = []

    for name, model in MODEL_MAP.items():
        target = SCHEMAS_DIR / f"{name}.schema.json"
        rendered = render(name, model)
        if args.check:
            existing = target.read_text() if target.exists() else ""
            if existing != rendered:
                drift.append(target.name)
        else:
            target.write_text(rendered)
            print(f"wrote {target.relative_to(SCHEMAS_DIR.parent)}")

    if args.check and drift:
        print("Schemas out of date:", ", ".join(drift), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
