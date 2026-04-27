"""CLI parsing helpers for per-role runtime overrides."""

from __future__ import annotations

from ..config.profiles import validate_reasoning, validate_runtime_role


def parse_role_assignments(
    values: list[str] | None, *, validate_values: bool = False
) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw in values or []:
        if "=" not in raw:
            raise ValueError(f"expected ROLE=VALUE, got {raw!r}")
        role, value = raw.split("=", 1)
        role = validate_runtime_role(role.strip())
        value = value.strip()
        if not value:
            raise ValueError(f"empty value for role {role!r}")
        if validate_values:
            value = validate_reasoning(value, label=f"role {role!r} reasoning")
        parsed[role] = value
    return parsed
