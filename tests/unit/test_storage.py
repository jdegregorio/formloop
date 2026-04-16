from __future__ import annotations

from formloop.models import EffectiveRuntime, RunRecord
from formloop.storage.files import FileRunStore


def test_file_run_store_round_trip(tmp_path) -> None:
    store = FileRunStore(tmp_path)
    record = RunRecord(
        prompt="hello",
        effective_runtime=EffectiveRuntime(
            profile="normal",
            provider="openai_responses",
            model="gpt-5.4",
            thinking="high",
            backend="heuristic",
        ),
    )
    store.create_run(record)
    loaded = store.load_run(record.run_id)
    assert loaded.run_id == record.run_id
    assert loaded.prompt == "hello"

