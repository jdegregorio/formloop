from __future__ import annotations

from pathlib import Path

from formloop.config import load_config, required_env_vars


def test_load_config_supports_run_store_override(configured_env: Path) -> None:
    config = load_config(configured_env)
    assert config.app.run_store.endswith(".formloop-test")
    assert config.profile("normal").model == "gpt-5.4"


def test_required_env_vars_cover_openai_and_anthropic_profiles(configured_env: Path) -> None:
    config = load_config(configured_env)
    env_vars = required_env_vars(config, ["normal", "anthropic_normal"])
    assert env_vars == ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]

