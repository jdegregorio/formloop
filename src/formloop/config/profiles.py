"""Profile and harness configuration loading.

REQ: FLH-D-014, FLH-D-017, FLH-NF-008
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from .env import repo_root

CONFIG_FILENAME = "formloop.harness.toml"
ReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh"]
REASONING_EFFORTS: frozenset[str] = frozenset(("none", "minimal", "low", "medium", "high", "xhigh"))


@dataclass(frozen=True, slots=True)
class Profile:
    name: str
    model: str
    reasoning: ReasoningEffort
    description: str = ""


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
    runs_dir: Path
    evals_dir: Path
    timeouts: Timeouts
    profiles: dict[str, Profile]
    api: ApiConfig
    repo_root: Path

    def profile(self, name: str | None = None) -> Profile:
        n = name or self.default_profile
        if n not in self.profiles:
            raise KeyError(f"unknown profile {n!r}; known: {sorted(self.profiles)}")
        return self.profiles[n]


def load_config(path: Path | None = None) -> HarnessConfig:
    """Parse ``formloop.harness.toml`` into a typed config object."""

    root = repo_root()
    cfg_path = path if path is not None else root / CONFIG_FILENAME
    with cfg_path.open("rb") as fh:
        data = tomllib.load(fh)

    profiles: dict[str, Profile] = {}
    for name, entry in data.get("profiles", {}).items():
        reasoning = str(entry["reasoning"])
        if reasoning not in REASONING_EFFORTS:
            raise ValueError(
                f"profile {name!r} has unsupported reasoning={reasoning!r}; "
                f"expected one of {sorted(REASONING_EFFORTS)}"
            )
        profiles[name] = Profile(
            name=name,
            model=str(entry["model"]),
            reasoning=cast(ReasoningEffort, reasoning),
            description=str(entry.get("description", "")),
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
        max_revisions=int(data.get("max_revisions", 3)),
        runs_dir=(root / str(data.get("runs_dir", "var/runs"))).resolve(),
        evals_dir=(root / str(data.get("evals_dir", "var/evals"))).resolve(),
        timeouts=timeouts,
        profiles=profiles,
        api=api,
        repo_root=root,
    )
