"""Narrator service — wraps the Narrator agent for the orchestrator.

REQ: FLH-F-024, FLH-F-026, FLH-NF-010

The orchestrator never calls the Narrator agent directly. It calls
``Narrator.narrate(...)`` which:

* awaits the agent with a per-call timeout, then returns ``(text, None)``;
* on any exception or timeout returns ``(fallback, error_str)`` so a
  flaky narrator never aborts a run (FLH-NF-010);
* honors a ``fallback_only`` mode that skips the LLM call entirely — used
  by tests, ``dev_test`` smoke runs, and any environment without an
  ``OPENAI_API_KEY``.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from ..agents import build_narrator
from ..agents.common import Runner
from ..agents.narrator import NarrationInput, NarrationOutput
from ..config.profiles import Profile

DEFAULT_TIMEOUT_SECONDS = 10.0


class Narrator:
    """Generates conversational status updates from milestone payloads."""

    def __init__(
        self,
        *,
        profile: Profile | None = None,
        fallback_only: bool = False,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.fallback_only = fallback_only
        self.timeout_seconds = timeout_seconds
        # Build the agent eagerly so construction errors surface up-front,
        # but only when we actually intend to call it.
        self._agent: Any | None = None if fallback_only else build_narrator(profile)

    @classmethod
    def auto(cls, *, profile: Profile | None = None) -> "Narrator":
        """Choose ``fallback_only`` automatically based on the environment.

        Used by the CLI / API entry points so a missing ``OPENAI_API_KEY``
        degrades to fallback strings instead of raising.
        """

        if not os.environ.get("OPENAI_API_KEY"):
            return cls(fallback_only=True)
        return cls(profile=profile)

    async def narrate(
        self, payload: NarrationInput, *, fallback: str
    ) -> tuple[str, str | None]:
        """Return ``(text, error)`` for one milestone.

        ``error`` is ``None`` on success and a short string when the
        narrator failed and the fallback was substituted.
        """

        if self.fallback_only or self._agent is None:
            return fallback, None
        try:
            result = await asyncio.wait_for(
                Runner.run(self._agent, input=payload.model_dump_json()),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError:
            return fallback, f"timeout after {self.timeout_seconds:.1f}s"
        except Exception as exc:  # noqa: BLE001 -- never abort the run
            return fallback, f"{type(exc).__name__}: {exc}"[:200]

        out = result.final_output
        if isinstance(out, NarrationOutput):
            text = (out.text or "").strip()
        else:
            # Defensive: SDK may surface str under non-strict output.
            text = str(out).strip()
        if not text:
            return fallback, "empty narration"
        return text, None


__all__ = ["DEFAULT_TIMEOUT_SECONDS", "Narrator"]
