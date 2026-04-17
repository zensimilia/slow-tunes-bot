import sys

from loguru import logger

from .config import config

LOG_LEVEL = "DEBUG" if config.DEBUG else "INFO"


def setup_logging() -> None:
    """
    Sets up logging configuration with a specific format and log level.
    """

    logger.remove()  # Remove a previously added handlers
    logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        filter=lambda r: r["level"].no < logger.level("ERROR").no,
        colorize=True,
    )
    logger.add(
        sys.stderr,
        level="ERROR",
        colorize=True,
    )
