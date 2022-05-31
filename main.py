from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from bot.config import AppConfig
from bot.db import init_sqlite
from bot.handlers import register_handlers

config = AppConfig()
storage = MemoryStorage()


async def on_startup(dp: Dispatcher):
    """Execute function before Bot start polling."""

    init_sqlite()
    register_handlers(dp)

    commands = [
        types.BotCommand('random', 'get some slowed tune'),
        types.BotCommand('help', 'if you stuck'),
        types.BotCommand('about', 'bot info'),
    ]
    await dp.bot.set_my_commands(commands)


async def on_shutdown(_dp: Dispatcher):
    """Execute function before Bot shut down polling."""


def main():
    """Main app runner."""

    bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
    dp = Dispatcher(bot, storage=storage)

    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
    )


if __name__ == '__main__':
    main()
