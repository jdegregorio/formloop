"""Generate checked-in JSON Schema files from runtime models."""

from __future__ import annotations

from formloop.jsonutil import dumps_json
from formloop.models import schema_models
from formloop.paths import schema_root


def main() -> None:
    target_root = schema_root()
    target_root.mkdir(parents=True, exist_ok=True)
    for name, model in schema_models().items():
        target = target_root / f"{name}.schema.json"
        target.write_text(dumps_json(model.model_json_schema()), encoding="utf-8")
        print(f"wrote {target}")


if __name__ == "__main__":
    main()
