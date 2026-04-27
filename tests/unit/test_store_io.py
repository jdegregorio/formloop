from __future__ import annotations

import json
import importlib.util
import os
import stat
import threading
from pathlib import Path

import pytest


def _load_atomic_write_text():
    module_path = Path(__file__).resolve().parents[2] / "src/formloop/store/io.py"
    spec = importlib.util.spec_from_file_location("formloop.store.io", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.atomic_write_text


atomic_write_text = _load_atomic_write_text()


def test_atomic_write_text_threaded_stress_writes_valid_json(tmp_path: Path) -> None:
    target = tmp_path / "run.json"
    writer_errors: list[Exception] = []
    reader_errors: list[Exception] = []

    writer_count = 8
    writes_per_writer = 150
    start = threading.Barrier(writer_count + 1)
    done = threading.Event()

    def writer(writer_id: int) -> None:
        start.wait()
        for iteration in range(writes_per_writer):
            payload = {
                "writer": writer_id,
                "iteration": iteration,
                "message": "atomic-write",
                "padding": "x" * 4096,
            }
            try:
                atomic_write_text(target, json.dumps(payload))
            except Exception as exc:  # pragma: no cover - asserted below
                writer_errors.append(exc)
                return

    def reader() -> None:
        while not done.is_set():
            try:
                data = target.read_text(encoding="utf-8")
            except FileNotFoundError:
                continue
            try:
                json.loads(data)
            except json.JSONDecodeError as exc:  # pragma: no cover - asserted below
                reader_errors.append(exc)
                return

    reader_thread = threading.Thread(target=reader, daemon=True)
    reader_thread.start()

    writers = [threading.Thread(target=writer, args=(idx,)) for idx in range(writer_count)]
    for thread in writers:
        thread.start()

    start.wait()
    for thread in writers:
        thread.join()
    done.set()
    reader_thread.join()

    assert not writer_errors
    assert not reader_errors

    final_payload = json.loads(target.read_text(encoding="utf-8"))
    assert final_payload["message"] == "atomic-write"
    assert len(final_payload["padding"]) == 4096


@pytest.mark.skipif(os.name != "posix", reason="POSIX permissions semantics")
def test_atomic_write_text_preserves_existing_file_permissions(tmp_path: Path) -> None:
    target = tmp_path / "snapshot.json"
    target.write_text('{"initial":true}', encoding="utf-8")
    target.chmod(0o644)

    atomic_write_text(target, '{"updated":true}')

    assert stat.S_IMODE(target.stat().st_mode) == 0o644


@pytest.mark.skipif(os.name != "posix", reason="POSIX directory fsync semantics")
def test_atomic_write_text_swallows_parent_open_fail_after_replace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "run.json"
    real_open = os.open

    def open_that_fails_for_directory(path: str | os.PathLike[str], flags: int, *args: object) -> int:
        if Path(path) == target.parent:
            raise OSError("cannot open parent")
        return real_open(path, flags, *args)

    monkeypatch.setattr(os, "open", open_that_fails_for_directory)

    atomic_write_text(target, '{"ok":true}')

    assert json.loads(target.read_text(encoding="utf-8"))["ok"] is True


@pytest.mark.skipif(os.name != "posix", reason="POSIX umask semantics")
def test_atomic_write_text_new_file_does_not_mutate_process_umask(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "new.json"
    original_umask = os.umask(0o027)
    os.umask(original_umask)

    def fail_if_called(mask: int) -> int:
        raise AssertionError(f"os.umask should not be called, got {mask:o}")

    monkeypatch.setattr(os, "umask", fail_if_called)

    atomic_write_text(target, '{"ok":true}')

    assert json.loads(target.read_text(encoding="utf-8"))["ok"] is True
