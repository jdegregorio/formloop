"""Formloop operator CLI entry point.

REQ: FLH-F-012, FLH-F-013, FLH-D-015, FLH-D-016, FLH-NF-004
"""

from .commands import app

__all__ = ["app"]


def main() -> None:  # pragma: no cover
    app()
