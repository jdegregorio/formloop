"""Known Build123D ecosystem libraries available to the harness."""

from __future__ import annotations

AVAILABLE_BUILD123D_LIBRARIES: tuple[str, ...] = (
    "bd_warehouse",
    "bd_vslot",
    "py_gearworks",
)


def available_build123d_libraries_text() -> str:
    """Human-readable comma-separated list for prompts/instructions."""

    return ", ".join(AVAILABLE_BUILD123D_LIBRARIES)


__all__ = ["AVAILABLE_BUILD123D_LIBRARIES", "available_build123d_libraries_text"]
