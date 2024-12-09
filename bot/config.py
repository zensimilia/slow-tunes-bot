import math
import os
import sys

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """
    Global application configurations.
    Variables will be loaded from the .env file. However, if
    there is a shell environment variable having the same name,
    that will take precedence.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    ADMIN_ID: int
    ALBUM_ART: str = "./assets/thumb.jpg"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 3001
    BOT_TOKEN: str
    DATA_DIR: str = "./data/"
    DB_FILE: str = os.path.join(DATA_DIR, "db.sqlite")
    DEBUG: bool = False
    SPEED_RATIO: float = 33 / 45
    PITCH_RATIO: float = -12 * math.log(1 / SPEED_RATIO, 2)  # Not used yet
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    TASK_LIMIT: int = 2
    THROTTLE_RATE: int = 15  # In seconds
    USE_WEBHOOK: bool = False
    WEBHOOK_HOST: str = "localhost"
    WEBHOOK_PATH: str = "/"
    WEBHOOK_URL: str = f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}"

try:
    config = AppConfig.model_validate({})
except ValidationError as err:
    sys.exit(1)
