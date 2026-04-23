"""Compatibility entrypoint for CLI app assembly.

This module forwards to :mod:`formloop.cli.commands` package assembly.
"""

from __future__ import annotations

from .commands import app

__all__ = ["app"]
