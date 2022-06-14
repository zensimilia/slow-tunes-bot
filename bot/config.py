import math
import os

from pydantic import BaseSettings


class AppConfig(BaseSettings):
    """Global application configurations.
    Variables will be loaded from the .env file. However, if
    there is a shell environment variable having the same name,
    that will take precedence.
    """

    DEBUG: bool = False
    BOT_TOKEN: str = ""
    DATA_DIR: str = "./data/"
    DB_FILE: str = os.path.join(DATA_DIR, "db.sqlite")
    SPEED_RATIO: float = 33 / 45
    PITCH_RATIO: float = -12 * math.log(1 / SPEED_RATIO, 2)  # Not used yet
    THROTTLE_RATE: int = 15  # In seconds
    ALBUM_ART: str = "./assets/thumb.jpg"

    class Config:
        """Load variables from the dotenv file."""

        env_file: str = ".env"
        env_file_encoding: str = "utf-8"
