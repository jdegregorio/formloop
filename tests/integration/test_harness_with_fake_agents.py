from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from formloop.models import (
    CadDesignOutput,
    ManagerNormalizationOutput,
    NormalizedSpec,
    ResearchFinding,
    ResearchTopic,
    ReviewDecision,
    ReviewSummary,
    RunCreateRequest,
)
from formloop.services.harness import HarnessService


class FakeHarnessService(HarnessService):
    async def _run_manager_normalization(self, **kwargs):
        return ManagerNormalizationOutput(
            input_summary="cube",
            current_spec=NormalizedSpec(
                intent_summary="A 20 mm cube.",
                dimensions_constraints=["20 mm x 20 mm x 20 mm"],
                required_features=["Single solid cube"],
                assumptions=["Centered at origin is acceptable."],
            ),
            assumptions=["Centered at origin is acceptable."],
            research_topics=[],
            initial_execution_plan=["Create the first revision."],
        )

    async def _design_revision_source(self, **kwargs):
        return CadDesignOutput(
            model_name="cube",
            strategy="Simple cube",
            source_code=(
                "from build123d import Box\n\n"
                "def build_model(params, context):\n"
                "    return Box(20, 20, 20)\n"
            ),
            notes=[],
        )

    async def _review_revision(self, **kwargs):
        return ReviewSummary(
            decision=ReviewDecision.accept,
            confidence=0.9,
            key_findings=["Matches the requested cube shape."],
            suspect_or_missing_features=[],
            suspect_dimensions_to_recheck=[],
            revision_instructions=[],
            summary="Accepted.",
        )

    async def _final_delivery_message(self, **kwargs):
        return "Delivered cube."


def test_flh_f_005_and_flh_v_002_harness_persists_revision_bundle(
    test_config,
    tmp_path: Path,
) -> None:
    service = FakeHarnessService(config=test_config)
    outcome = service.run_sync(RunCreateRequest(prompt="Create a 20 mm cube.", profile="dev_test"))
    run_dir = service.store.run_dir(outcome.run.run_name)
    revision_dir = run_dir / "revisions" / "rev-001"
    assert outcome.run.status.value == "completed"
    assert (run_dir / "run.json").exists()
    assert (run_dir / "events.jsonl").exists()
    assert (revision_dir / "step.step").exists()
    assert (revision_dir / "render-sheet.png").exists()
    assert (revision_dir / "review-summary.json").exists()


class FakeResearchHarness(FakeHarnessService):
    async def _run_manager_normalization(self, **kwargs):
        return ManagerNormalizationOutput(
            input_summary="research cube",
            current_spec=NormalizedSpec(
                intent_summary="A cube that requires researched context.",
                dimensions_constraints=["20 mm x 20 mm x 20 mm"],
                required_features=["Single solid cube"],
                assumptions=["Centered at origin is acceptable."],
            ),
            assumptions=["Centered at origin is acceptable."],
            research_topics=[
                ResearchTopic(
                    topic_id="topic-1",
                    question="What is a typical M6 clearance hole size?",
                    reason="Hole sizing convention",
                ),
                ResearchTopic(
                    topic_id="topic-2",
                    question="What is a typical edge margin for simple brackets?",
                    reason="Bracket convention",
                ),
            ],
            initial_execution_plan=["Research first, then create the revision."],
        )


def test_flh_f_016_through_flh_f_018_research_is_fanned_out_and_persisted(
    test_config,
    monkeypatch,
) -> None:
    async def fake_runner_run(agent, payload, context=None, hooks=None):
        del agent, context, hooks
        text = payload if isinstance(payload, str) else str(payload)
        if "topic_id=topic-1" in text:
            output = ResearchFinding(
                topic_id="topic-1",
                summary="Use a 6.5 mm clearance hole for an M6 fastener.",
                citations=[],
            )
        else:
            output = ResearchFinding(
                topic_id="topic-2",
                summary=(
                    "A simple bracket often keeps at least one material thickness of edge margin."
                ),
                citations=[],
            )
        return SimpleNamespace(final_output=output)

    monkeypatch.setattr("formloop.services.harness.Runner.run", fake_runner_run)
    service = FakeResearchHarness(config=test_config)
    outcome = service.run_sync(
        RunCreateRequest(prompt="Create a researched cube.", profile="dev_test")
    )
    run_dir = service.store.run_dir(outcome.run.run_name)
    research_file = run_dir / "research" / "research-findings.json"
    assert research_file.exists()
    events = [event.event_type for event in service.store.list_events(outcome.run.run_name)]
    assert "research_started" in events
    assert "research_completed" in events
