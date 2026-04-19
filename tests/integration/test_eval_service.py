from __future__ import annotations

from formloop.models import (
    EvalPassStatus,
)
from formloop.services.evals import EvalService
from formloop.services.harness import HarnessOutcome, HarnessService


class FakeEvalHarness(HarnessService):
    async def run(self, request):
        run = self.begin_run(request)
        revision, revision_dir = self.store.create_revision(run=run, trigger="eval")
        step_path = revision_dir / "step.step"
        step_path.write_text("dummy", encoding="utf-8")
        render_sheet = revision_dir / "render-sheet.png"
        render_sheet.write_bytes(b"png")
        revision.review_summary_path = str(revision_dir / "review-summary.json")
        revision_dir.joinpath("review-summary.json").write_text("{}", encoding="utf-8")
        run.revisions.append(revision)
        run.current_revision_id = revision.revision_id
        run.artifact_references = {"step": str(step_path), "render_sheet": str(render_sheet)}
        self.store.write_run(run)
        self.store.write_snapshot(self._materialize_snapshot(run), run_name=run.run_name)
        return HarnessOutcome(run=run, snapshot=self._materialize_snapshot(run), final_message="ok")


class FakeCadRuntime:
    def compare(self, **kwargs):
        return {"metrics": {"overlap_ratio": 1.0}}

    def run_json(self, *args):
        return {"data": {"volume": 1.0}}


class FakeEvalService(EvalService):
    async def _judge_case(self, **kwargs):
        fake_path = self._report_root() / "fake-judge.json"
        fake_path.write_text(
            '{"mode":"dev_eval","score":1.0,"pass_status":"pass","rationale":"ok","issues":[],"recommended_actions":[]}',
            encoding="utf-8",
        )
        return fake_path, EvalPassStatus.pass_


def test_flh_f_014_and_flh_v_008_eval_report_is_generated(test_config) -> None:
    service = FakeEvalService(
        config=test_config,
        harness=FakeEvalHarness(config=test_config),
        cad_runtime=FakeCadRuntime(),
    )
    report = service.run_dataset_sync("basic_shapes", profile="dev_test")
    assert report.total_cases >= 1
    assert report.passed_cases >= 1
