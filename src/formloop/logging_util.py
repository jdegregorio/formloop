"""Per-run file logging helpers.

Attach a ``FileHandler`` to the ``formloop`` logger for the duration of a run so
every ``logging.getLogger("formloop.*")`` call is captured to ``run.log`` inside
the run directory.

v1 assumes a single active run per process (the CLI case). If two runs share a
process their log lines will land in both files; a context-var filter can be
added later without changing callers.
"""

from __future__ import annotations

import logging
from pathlib import Path

_LOGGER_NAME = "formloop"
_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_DATEFMT = "%Y-%m-%dT%H:%M:%S%z"


def setup_run_logger(log_path: Path) -> logging.FileHandler:
    """Install a ``FileHandler`` on the ``formloop`` logger writing to ``log_path``."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.level == logging.NOTSET or logger.level > logging.DEBUG:
        logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return handler


def teardown_run_logger(handler: logging.FileHandler) -> None:
    """Detach and close a handler previously returned by :func:`setup_run_logger`."""
    logger = logging.getLogger(_LOGGER_NAME)
    try:
        handler.flush()
    except Exception:
        pass
    if handler in logger.handlers:
        logger.removeHandler(handler)
    try:
        handler.close()
    except Exception:
        pass
