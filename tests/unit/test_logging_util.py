"""Unit tests for per-run file logging helpers."""

from __future__ import annotations

import logging

from formloop.logging_util import setup_run_logger, teardown_run_logger


def test_setup_writes_messages_and_teardown_detaches(tmp_path) -> None:
    log_path = tmp_path / "run.log"
    handler = setup_run_logger(log_path)

    root = logging.getLogger("formloop")
    assert handler in root.handlers

    logging.getLogger("formloop.test").info("hello world")
    logging.getLogger("formloop.deep.nested").debug("debug line")

    teardown_run_logger(handler)
    assert handler not in root.handlers

    text = log_path.read_text()
    assert "hello world" in text
    assert "formloop.test" in text
    assert "INFO" in text
    assert "debug line" in text


def test_setup_creates_parent_dir(tmp_path) -> None:
    log_path = tmp_path / "nested" / "dir" / "run.log"
    handler = setup_run_logger(log_path)
    try:
        logging.getLogger("formloop.nested").info("x")
    finally:
        teardown_run_logger(handler)
    assert log_path.is_file()


def test_teardown_is_safe_on_empty_log(tmp_path) -> None:
    log_path = tmp_path / "run.log"
    handler = setup_run_logger(log_path)
    teardown_run_logger(handler)
    # Idempotent: calling again must not raise.
    teardown_run_logger(handler)
    assert logging.getLogger("formloop").handlers.count(handler) == 0


def test_does_not_capture_non_formloop_loggers(tmp_path) -> None:
    log_path = tmp_path / "run.log"
    handler = setup_run_logger(log_path)
    try:
        # Sibling logger outside the formloop namespace must not be captured.
        logging.getLogger("other.module").warning("should not appear")
        logging.getLogger("formloop.real").warning("should appear")
    finally:
        teardown_run_logger(handler)
    text = log_path.read_text()
    assert "should appear" in text
    assert "should not appear" not in text
