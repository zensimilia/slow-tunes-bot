import logging
import sys

from loguru import logger

from bot.config import config

LOG_LEVEL = "DEBUG" if config.DEBUG else "INFO"


class InterceptHandler(logging.Handler):
    """A logging handler that intercepts standard logging messages and redirects them to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 0

        while frame:
            filename = frame.f_code.co_filename
            if filename in (logging.__file__, __file__):
                frame = frame.f_back
                depth += 1
            else:
                break

        logger.opt(
            depth=depth,
            exception=record.exc_info,
        ).log(
            level,
            record.getMessage(),
        )


def setup_logging() -> None:
    """Sets up logging configuration with a specific format and log level."""

    logging.basicConfig(
        handlers=[InterceptHandler()],
        level=logging.DEBUG,
        force=True,
    )  # logging -> loguru

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

    logger.info("Loguru: logger configured and intercepts standart logging messages")
