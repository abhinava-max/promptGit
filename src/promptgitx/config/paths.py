"""Paths used by PromptGitX configuration."""

from __future__ import annotations

import os
from pathlib import Path


ENV_PATH_OVERRIDE = "PROMPTGITX_ENV_PATH"


def get_config_dir() -> Path:
    """Return the stable user-level PromptGitX configuration directory."""
    return Path.home() / ".promptgitx"


def get_config_env_path() -> Path:
    """Return the env file path used for PromptGitX settings.

    By default, PromptGitX stores LLM credentials in a user-level config file
    so running the CLI from different project folders does not create scattered
    `.env` files. `PROMPTGITX_ENV_PATH` can be used by tests or power users who
    explicitly want a different location.
    """
    override = os.environ.get(ENV_PATH_OVERRIDE, "").strip()

    if override:
        return Path(override).expanduser()

    return get_config_dir() / ".env"
