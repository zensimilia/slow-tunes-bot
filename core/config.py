import sys
from pathlib import Path

from loguru import logger
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global application configurations. Variables will be loaded from the .env file.
    However, if there is a shell environment variable having the same name, that will take precedence.
    """

    # class config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # required settings
    BOT_ADMIN_ID: int
    BOT_TOKEN: str
    BOT_MENTION: str | None = None

    # pathes
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DB_FILE: Path = DATA_DIR / "db.sqlite"

    # defaults
    DEBUG: bool = False
    LICENSE_URL: str = "https://github.com/zensimilia/slow-tunes-bot/blob/master/LICENSE"
    SOURCE_URL: str = "https://github.com/zensimilia/slow-tunes-bot"

    # redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379


try:
    config = Settings()  # type: ignore
except ValidationError as e:
    message = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors(include_input=False, include_url=False)])
    logger.critical(f"Configuration error: {message}")
    sys.exit(1)
