import math

from pydantic import BaseSettings


class AppConfig(BaseSettings):
    """Global application configurations.
    Variables will be loaded from the .env file. However, if
    there is a shell environment variable having the same name,
    that will take precedence.
    """

    BOT_TOKEN: str = ""
    DATA_DIR: str = "./data/"
    SPEED_RATIO: float = 33 / 45
    PITCH_RATIO: float = -12 * math.log(1 / SPEED_RATIO, 2)
    FILE_POSTFIX: str = "_slowed_down.mp3"

    class Config:
        """Load variables from the dotenv file."""

        env_file: str = '.env'
        env_file_encoding: str = 'utf-8'
