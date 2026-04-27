"""Profile and harness configuration loading.

REQ: FLH-D-014, FLH-D-017, FLH-NF-008
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, cast

from .env import repo_root

CONFIG_FILENAME = "formloop.harness.toml"
ReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh"]
REASONING_EFFORTS: frozenset[str] = frozenset(("none", "minimal", "low", "medium", "high", "xhigh"))
RuntimeRole = Literal[
    "manager_plan",
    "research",
    "cad_designer",
    "reviewer",
    "manager_final",
    "judge",
    "narrator",
]
RUNTIME_ROLES: tuple[RuntimeRole, ...] = (
    "manager_plan",
    "research",
    "cad_designer",
    "reviewer",
    "manager_final",
    "judge",
    "narrator",
)
RUNTIME_ROLE_SET: frozenset[str] = frozenset(RUNTIME_ROLES)


@dataclass(frozen=True, slots=True)
class Profile:
    name: str
    model: str
    reasoning: ReasoningEffort
    description: str = ""
    role_overrides: dict[str, RoleRuntimeOverride] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RoleRuntimeOverride:
    model: str | None = None
    reasoning: ReasoningEffort | None = None


@dataclass(frozen=True, slots=True)
class ApiConfig:
    host: str
    port: int
    pid_file: str
    log_file: str


@dataclass(frozen=True, slots=True)
class Timeouts:
    cad_build: int
    cad_render: int
    cad_inspect: int
    cad_compare: int
    agent_run: int


@dataclass(frozen=True, slots=True)
class HarnessConfig:
    default_profile: str
    max_revisions: int
    max_research_topics: int
    runs_dir: Path
    evals_dir: Path
    timeouts: Timeouts
    profiles: dict[str, Profile]
    api: ApiConfig
    repo_root: Path
    max_cad_designer_turns: int = 20

    def profile(self, name: str | None = None) -> Profile:
        n = name or self.default_profile
        if n not in self.profiles:
            raise KeyError(f"unknown profile {n!r}; known: {sorted(self.profiles)}")
        return self.profiles[n]

    def resolve_role_profile(
        self,
        profile: Profile,
        role: RuntimeRole | str,
        *,
        global_model: str | None = None,
        global_reasoning: ReasoningEffort | str | None = None,
        role_model_overrides: dict[str, str] | None = None,
        role_reasoning_overrides: dict[str, str] | None = None,
    ) -> Profile:
        role = validate_runtime_role(role)
        role_override = profile.role_overrides.get(role)
        model = profile.model
        reasoning: ReasoningEffort = profile.reasoning
        if role_override is not None:
            model = role_override.model or model
            reasoning = role_override.reasoning or reasoning
        if global_model:
            model = global_model
        if global_reasoning:
            reasoning = validate_reasoning(global_reasoning, label="global reasoning override")
        if role_model_overrides and role in role_model_overrides:
            model = role_model_overrides[role]
        if role_reasoning_overrides and role in role_reasoning_overrides:
            reasoning = validate_reasoning(
                role_reasoning_overrides[role], label=f"role {role!r} reasoning override"
            )
        return Profile(
            name=f"{profile.name}:{role}",
            model=model,
            reasoning=reasoning,
            description=f"{profile.name} runtime for {role}",
        )

    def resolve_role_profiles(
        self,
        profile: Profile,
        *,
        global_model: str | None = None,
        global_reasoning: ReasoningEffort | str | None = None,
        role_model_overrides: dict[str, str] | None = None,
        role_reasoning_overrides: dict[str, str] | None = None,
    ) -> dict[str, Profile]:
        for role in (role_model_overrides or {}).keys():
            validate_runtime_role(role)
        for role in (role_reasoning_overrides or {}).keys():
            validate_runtime_role(role)
        return {
            role: self.resolve_role_profile(
                profile,
                role,
                global_model=global_model,
                global_reasoning=global_reasoning,
                role_model_overrides=role_model_overrides,
                role_reasoning_overrides=role_reasoning_overrides,
            )
            for role in RUNTIME_ROLES
        }


def validate_runtime_role(role: str) -> RuntimeRole:
    if role not in RUNTIME_ROLE_SET:
        expected = ", ".join(sorted(RUNTIME_ROLE_SET))
        raise ValueError(f"unknown runtime role {role!r}; expected one of {expected}")
    return cast(RuntimeRole, role)


def validate_reasoning(value: str, *, label: str = "reasoning") -> ReasoningEffort:
    if value not in REASONING_EFFORTS:
        raise ValueError(f"{label}={value!r}; expected one of {sorted(REASONING_EFFORTS)}")
    return cast(ReasoningEffort, value)


def load_config(path: Path | None = None) -> HarnessConfig:
    """Parse ``formloop.harness.toml`` into a typed config object."""

    root = repo_root()
    cfg_path = path if path is not None else root / CONFIG_FILENAME
    with cfg_path.open("rb") as fh:
        data = tomllib.load(fh)

    profiles: dict[str, Profile] = {}
    for name, entry in data.get("profiles", {}).items():
        reasoning = str(entry["reasoning"])
        reasoning_effort = validate_reasoning(reasoning, label=f"profile {name!r} reasoning")
        role_overrides: dict[str, RoleRuntimeOverride] = {}
        for role, role_entry in entry.get("roles", {}).items():
            valid_role = validate_runtime_role(str(role))
            role_reasoning = role_entry.get("reasoning")
            role_overrides[valid_role] = RoleRuntimeOverride(
                model=str(role_entry["model"]) if "model" in role_entry else None,
                reasoning=(
                    validate_reasoning(
                        str(role_reasoning), label=f"profile {name!r} role {valid_role!r} reasoning"
                    )
                    if role_reasoning is not None
                    else None
                ),
            )
        profiles[name] = Profile(
            name=name,
            model=str(entry["model"]),
            reasoning=reasoning_effort,
            description=str(entry.get("description", "")),
            role_overrides=role_overrides,
        )

    if not profiles:
        raise ValueError(f"{cfg_path} must define at least one profile under [profiles.*]")

    timeouts_raw = data.get("timeouts", {})
    timeouts = Timeouts(
        cad_build=int(timeouts_raw.get("cad_build", 180)),
        cad_render=int(timeouts_raw.get("cad_render", 240)),
        cad_inspect=int(timeouts_raw.get("cad_inspect", 60)),
        cad_compare=int(timeouts_raw.get("cad_compare", 240)),
        agent_run=int(timeouts_raw.get("agent_run", 600)),
    )

    api_raw = data.get("api", {})
    api = ApiConfig(
        host=str(api_raw.get("host", "127.0.0.1")),
        port=int(api_raw.get("port", 8765)),
        pid_file=str(api_raw.get("pid_file", "var/formloop.pid")),
        log_file=str(api_raw.get("log_file", "var/formloop.log")),
    )

    default_profile = str(data.get("default_profile", "normal"))
    if default_profile not in profiles:
        raise ValueError(f"default_profile={default_profile!r} not defined in [profiles.*]")

    return HarnessConfig(
        default_profile=default_profile,
        max_revisions=int(data.get("max_revisions", 5)),
        max_research_topics=max(1, int(data.get("max_research_topics", 8))),
        max_cad_designer_turns=max(1, int(data.get("max_cad_designer_turns", 20))),
        runs_dir=(root / str(data.get("runs_dir", "var/runs"))).resolve(),
        evals_dir=(root / str(data.get("evals_dir", "var/evals"))).resolve(),
        timeouts=timeouts,
        profiles=profiles,
        api=api,
        repo_root=root,
    )
