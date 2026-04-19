"""Agent definitions.

REQ: FLH-D-007, FLH-D-008, FLH-D-009, FLH-D-010
"""

from .cad_designer import CadRevisionResult, build_cad_designer
from .common import PromptContext, RunContext, Runner
from .design_researcher import (
    ResearchCitation,
    ResearchFinding,
    build_design_researcher,
)
from .manager import (
    AssumptionProposal,
    ManagerFinalAnswer,
    ManagerPlan,
    build_manager_final,
    build_manager_plan,
)
from .quality_specialist import (
    build_quality_specialist_judge,
    build_quality_specialist_review,
)

__all__ = [
    "AssumptionProposal",
    "CadRevisionResult",
    "ManagerFinalAnswer",
    "ManagerPlan",
    "PromptContext",
    "ResearchCitation",
    "ResearchFinding",
    "RunContext",
    "Runner",
    "build_cad_designer",
    "build_design_researcher",
    "build_manager_final",
    "build_manager_plan",
    "build_quality_specialist_judge",
    "build_quality_specialist_review",
]
