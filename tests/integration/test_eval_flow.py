from __future__ import annotations


def test_eval_run_generates_batch_outputs(service) -> None:
    batch = service.execute_eval("basic_shapes", profile_name="eval")
    assert batch.aggregate_metrics["case_count"] == 1
    assert batch.case_results
    assert batch.report_path.endswith("latest.md")
    assert batch.case_results[0].deterministic_metrics
    assert batch.case_results[0].judge_outputs

