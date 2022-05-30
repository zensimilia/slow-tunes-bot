from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from bot.config import AppConfig

config = AppConfig()


def create_dispatcher() -> Dispatcher:
    """Create the instance of aiogram dispatcher."""

    bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
    return Dispatcher(bot, storage=MemoryStorage())
