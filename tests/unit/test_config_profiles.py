from __future__ import annotations

from pathlib import Path

import pytest

from formloop.config.profiles import (
    ApiConfig,
    HarnessConfig,
    Profile,
    RoleRuntimeOverride,
    Timeouts,
    load_config,
)


def _config(tmp_path: Path) -> HarnessConfig:
    return HarnessConfig(
        default_profile="normal",
        max_revisions=3,
        max_research_topics=8,
        runs_dir=tmp_path / "runs",
        evals_dir=tmp_path / "evals",
        timeouts=Timeouts(
            cad_build=1,
            cad_render=1,
            cad_inspect=1,
            cad_compare=1,
            agent_run=1,
        ),
        profiles={
            "normal": Profile(
                name="normal",
                model="base-model",
                reasoning="medium",
                role_overrides={
                    "cad_designer": RoleRuntimeOverride(model="cad-model", reasoning="high"),
                    "reviewer": RoleRuntimeOverride(reasoning="low"),
                },
            )
        },
        api=ApiConfig(host="127.0.0.1", port=0, pid_file="x.pid", log_file="x.log"),
        repo_root=tmp_path,
    )


def test_role_runtime_override_precedence(tmp_path: Path) -> None:
    config = _config(tmp_path)
    profile = config.profile("normal")

    roles = config.resolve_role_profiles(
        profile,
        global_model="global-model",
        global_reasoning="low",
        role_model_overrides={"cad_designer": "cli-cad-model"},
        role_reasoning_overrides={"reviewer": "xhigh"},
    )

    assert roles["manager_plan"].model == "global-model"
    assert roles["manager_plan"].reasoning == "low"
    assert roles["cad_designer"].model == "cli-cad-model"
    assert roles["cad_designer"].reasoning == "low"
    assert roles["reviewer"].model == "global-model"
    assert roles["reviewer"].reasoning == "xhigh"


def test_role_override_from_config_without_global_override(tmp_path: Path) -> None:
    config = _config(tmp_path)
    roles = config.resolve_role_profiles(config.profile("normal"))

    assert roles["cad_designer"].model == "cad-model"
    assert roles["cad_designer"].reasoning == "high"
    assert roles["reviewer"].model == "base-model"
    assert roles["reviewer"].reasoning == "low"
    assert roles["judge"].model == "base-model"
    assert roles["judge"].reasoning == "medium"


def test_invalid_runtime_role_is_rejected(tmp_path: Path) -> None:
    config = _config(tmp_path)
    with pytest.raises(ValueError, match="unknown runtime role"):
        config.resolve_role_profiles(config.profile("normal"), role_model_overrides={"bad": "x"})


def test_load_config_parses_profile_role_overrides(tmp_path: Path) -> None:
    cfg = tmp_path / "formloop.harness.toml"
    cfg.write_text(
        """
default_profile = "normal"
max_revisions = 3
max_research_topics = 8
max_cad_designer_turns = 20
runs_dir = "var/runs"
evals_dir = "var/evals"

[profiles.normal]
model = "base"
reasoning = "medium"

[profiles.normal.roles.cad_designer]
model = "cad"
reasoning = "high"
""",
        encoding="utf-8",
    )

    loaded = load_config(cfg)
    role = loaded.profile("normal").role_overrides["cad_designer"]
    assert role.model == "cad"
    assert role.reasoning == "high"
    assert loaded.max_cad_designer_turns == 20

