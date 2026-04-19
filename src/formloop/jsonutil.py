"""JSON serialization helpers."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def to_jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [to_jsonable(item) for item in value]
    return value


def dumps_json(data: Any) -> str:
    return json.dumps(to_jsonable(data), indent=2, sort_keys=True)
