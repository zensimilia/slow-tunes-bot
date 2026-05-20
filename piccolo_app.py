from piccolo.conf.apps import AppConfig

from bot.config import config
from models import Like, Match, User

MIGRATIONS_FOLDER = config.BASE_DIR / "migrations"

APP_CONFIG = AppConfig(
    app_name=config.APP_NAME,
    migrations_folder_path=MIGRATIONS_FOLDER,
    table_classes=[Like, Match, User],
    migration_dependencies=[],
    commands=[],
)
