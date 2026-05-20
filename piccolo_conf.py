from piccolo.conf.apps import AppRegistry
from piccolo.engine.sqlite import SQLiteEngine

from bot.config import config

DB = SQLiteEngine(path=config.DB_FILE.as_posix(), timeout=60)
APP_REGISTRY = AppRegistry(apps=["piccolo_app"])
