"""Configuration loading for Formloop."""

from __future__ import annotations

import os
import tomllib
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .bootstrap import bootstrap_environment
from .paths import repo_root


class ProfileConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str
    reasoning: str
    model_path: str = "responses"
    max_revisions: int = Field(default=3, ge=1, le=10)


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_profile: str
    run_root: str = "var/runs"
    max_revision_attempts: int = Field(default=3, ge=1, le=10)
    build_repair_attempts: int = Field(default=2, ge=0, le=10)
    http_host: str = "127.0.0.1"
    http_port: int = Field(default=8123, ge=1, le=65535)


class HarnessConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runtime: RuntimeConfig
    profiles: dict[str, ProfileConfig]

    @model_validator(mode="after")
    def validate_default_profile(self) -> HarnessConfig:
        if self.runtime.default_profile not in self.profiles:
            raise ValueError(
                f"default_profile {self.runtime.default_profile!r} not found in profiles"
            )
        if {"normal", "dev_test"} - set(self.profiles):
            raise ValueError("config must include profiles 'normal' and 'dev_test'")
        return self

    def profile(self, name: str | None = None) -> ProfileConfig:
        selected = name or self.runtime.default_profile
        try:
            return self.profiles[selected]
        except KeyError as exc:
            raise KeyError(f"unknown profile: {selected}") from exc

    def run_root_path(self) -> Path:
        return repo_root() / self.runtime.run_root


@lru_cache(maxsize=1)
def load_config(path: Path | None = None) -> HarnessConfig:
    bootstrap_environment()
    config_path = path or repo_root() / "formloop.harness.toml"
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)
    return HarnessConfig.model_validate(raw)


def require_openai_api_key() -> str:
    bootstrap_environment()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required")
    return api_key
