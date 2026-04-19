from __future__ import annotations

import os

from formloop.bootstrap import bootstrap_environment
from formloop.config import load_config
from formloop.paths import repo_root, sibling_cad_cli_root


def test_flh_d_014_and_flh_d_017_config_profiles_load() -> None:
    config = load_config()
    assert config.runtime.default_profile == "normal"
    assert {"normal", "dev_test"} <= set(config.profiles)
    assert config.profile("normal").model == "gpt-5.4"
    assert config.profile("dev_test").model == "gpt-5.4-nano"


def test_repo_paths_are_resolved_inside_formloop_repo() -> None:
    assert repo_root().name == "formloop"
    assert sibling_cad_cli_root().name == "cad-cli"


def test_flh_d_016_env_bootstrap_keeps_openai_key_visible() -> None:
    bootstrap_environment()
    assert "OPENAI_API_KEY" in os.environ
