from __future__ import annotations

import json

from formloop.models import schema_models
from formloop.paths import schema_root


def test_flh_d_021_and_flh_d_022_checked_in_schemas_match_runtime_models() -> None:
    for name, model in schema_models().items():
        expected = model.model_json_schema()
        actual = json.loads((schema_root() / f"{name}.schema.json").read_text(encoding="utf-8"))
        assert actual == expected
