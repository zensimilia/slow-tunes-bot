import inspect
import logging

from bot.config import AppConfig

config = AppConfig()

logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s [%(levelname)-8s] %(name)s <%(funcName)s:%(lineno)d> %(message)s',
)


def get_logger(name: str | None = None) -> logging.Logger:
    """Get the Logger instance with defaults."""

    if not name:
        stack = inspect.stack()[1]
        module = inspect.getmodule(stack[0])
        name = module.__name__ if module else __name__

    return logging.getLogger(name)
