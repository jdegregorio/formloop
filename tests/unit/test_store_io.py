from __future__ import annotations

import json
import importlib.util
import threading
from pathlib import Path


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
