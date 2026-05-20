import sys
from pathlib import Path
from typing import Self

from loguru import logger
from pydantic import Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global application configurations.

    Variables will be loaded from the .env file. However, if there is a shell environment variable
    having the same name, that will take precedence.
    """

    # class config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # required settings
    BOT_ADMIN_ID: int = Field(default=...)
    BOT_TOKEN: str = Field(default=...)
    BOT_MENTION: str | None = Field(default=None)

    # network
    TELEGRAM_PROXY_URL: str | None = Field(default=None)

    # pathes
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DB_FILE: Path = DATA_DIR / "db.sqlite"

    # defaults
    APP_NAME: str = "slow-tunes-bot"
    DEBUG: bool = False
    QUEUE_MAXSIZE: int = 2
    LICENSE_URL: str = "https://github.com/zensimilia/slow-tunes-bot/blob/master/LICENSE"
    SOURCE_URL: str = "https://github.com/zensimilia/slow-tunes-bot"

    # redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    @model_validator(mode="after")
    def create_data_dir(self) -> Self:
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        return self


try:
    config = Settings()
except ValidationError as e:
    message = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors(include_input=False, include_url=False)])
    logger.critical(f"Configuration error: {message}")
    sys.exit(1)
