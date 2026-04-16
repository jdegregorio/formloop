from __future__ import annotations

import os
import tomllib
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from formloop.types import ProviderKind, ThinkingLevel


class AppConfig(BaseModel):
    name: str
    run_store: str
    default_profile: str
    api_host: str
    api_port: int
    cad_command: str
    llm_backend: str
    ui_server_import: str


class RuntimeConfig(BaseModel):
    max_review_revisions: int = 2
    load_dotenv: bool = True
    dotenv_file: str = ".env.local"


class DatasetConfig(BaseModel):
    root: str = "datasets"


class SkillConfig(BaseModel):
    builtin_dir: str


class RunProfile(BaseModel):
    provider: ProviderKind
    model: str
    thinking: ThinkingLevel = ThinkingLevel.MEDIUM


class HarnessConfig(BaseModel):
    app: AppConfig
    profiles: dict[str, RunProfile]
    skills: SkillConfig
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    datasets: DatasetConfig = Field(default_factory=DatasetConfig)
    config_path: Path
    project_root: Path

    @property
    def run_store_path(self) -> Path:
        return (self.project_root / self.app.run_store).resolve()

    def profile(self, name: str | None = None) -> RunProfile:
        profile_name = name or self.app.default_profile
        try:
            return self.profiles[profile_name]
        except KeyError as exc:
            raise KeyError(f"Unknown profile '{profile_name}'") from exc


def load_config(project_root: Path | None = None) -> HarnessConfig:
    root = (project_root or Path.cwd()).resolve()
    config_path = root / "formloop.harness.toml"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file: {config_path}")

    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    runtime = raw.get("runtime", {})
    if runtime.get("load_dotenv", True):
        dotenv_path = root / runtime.get("dotenv_file", ".env.local")
        if dotenv_path.exists():
            load_dotenv(dotenv_path, override=False)

    data = dict(raw)
    data["config_path"] = config_path
    data["project_root"] = root
    config = HarnessConfig.model_validate(data)
    run_store_override = os.getenv("FORMLOOP_RUN_STORE")
    if run_store_override:
        config.app.run_store = run_store_override
    return config


def required_env_vars(config: HarnessConfig, profile_names: list[str] | None = None) -> list[str]:
    names = profile_names or list(config.profiles)
    env_vars: set[str] = set()
    for name in names:
        profile = config.profile(name)
        if profile.provider == ProviderKind.OPENAI_RESPONSES:
            env_vars.add("OPENAI_API_KEY")
        elif profile.provider == ProviderKind.LITELLM and profile.model.startswith("anthropic/"):
            env_vars.add("ANTHROPIC_API_KEY")
    return sorted(env_vars)


def env_snapshot(variable_names: list[str]) -> dict[str, bool]:
    return {name: bool(os.getenv(name)) for name in variable_names}
