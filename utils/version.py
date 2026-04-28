import tomllib
from functools import cache
from pathlib import Path

from loguru import logger

from core.config import config

FALLBACK_VERSION = "latest"


@cache
def get_app_version() -> str:
    """Return the application version from pyproject.toml or fallback to a default value."""

    toml_path = config.BASE_DIR / "pyproject.toml"
    try:
        with Path.open(toml_path, "rb") as file:
            data = tomllib.load(file)
        return data["project"]["version"]
    except (OSError, ValueError, KeyError) as err:
        logger.warning(f"Failed to read version from {toml_path}: {err}. Using fallback: {FALLBACK_VERSION}")
        return FALLBACK_VERSION
