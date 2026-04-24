"""Shared orchestration phase context contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from ..agents import RunContext
from ..agents.cad_designer import CadRevisionResult
from ..agents.manager import ManagerFinalAnswer, ManagerPlan
from ..config.profiles import Profile
from ..schemas import ProgressEventKind, ReviewSummary


class OrchestrationPhaseContext(Protocol):
    async def narrate(
        self,
        run_name: str,
        *,
        phase: str,
        just_completed: str,
        next_step: str,
        why: str,
        signals: dict[str, Any],
        fallback: str,
        context: dict[str, Any] | None = None,
    ) -> None: ...

    def emit(
        self,
        run_name: str,
        kind: ProgressEventKind,
        message: str,
        *,
        data: dict | None = None,
        phase: str | None = None,
        narration_error: str | None = None,
    ) -> None: ...

    def load_run(self, run_name: str): ...

    def save_run(self, run) -> None: ...

    def attach_review(self, run, revision_name: str, review: ReviewSummary) -> None: ...

    def persist_revision(self, run, bundle): ...

    def load_snapshot(self, run_name: str): ...

    async def plan(self, prompt: str, profile: Profile) -> ManagerPlan: ...

    async def research_topic(self, topic: str, profile: Profile) -> dict[str, Any]: ...

    async def design_revision(
        self, designer_input: str, run_ctx: RunContext, profile: Profile
    ) -> CadRevisionResult: ...

    async def review_revision(
        self,
        payload: list[dict[str, Any]],
        profile: Profile,
    ) -> ReviewSummary: ...

    async def finalize(self, payload: dict[str, Any], profile: Profile) -> ManagerFinalAnswer: ...


class PhaseRuntimeContext:
    def __init__(self, *, run, run_ctx: RunContext, profile: Profile, user_prompt: str) -> None:
        self.run = run
        self.run_ctx = run_ctx
        self.profile = profile
        self.user_prompt = user_prompt

    @property
    def run_root(self) -> Path:
        return self.run_ctx.run_root
