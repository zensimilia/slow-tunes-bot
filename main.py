import asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from bot.config import AppConfig
from bot.db import init_sqlite
from bot.handlers import register_handlers
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.utils.logger import get_logger
from bot.utils.queue import Queue

log = get_logger()
config = AppConfig()
queue = Queue()


async def on_startup(dp: Dispatcher):
    """Execute function before Bot start polling."""

    log.info("Execute startup Bot functions...")
    init_sqlite()
    register_handlers(dp)

    commands = [
        types.BotCommand("random", "get some slowed tune"),
        types.BotCommand("donate", "buy me a beer"),
        types.BotCommand("help", "if you stuck"),
        types.BotCommand("about", "bot info"),
    ]
    await dp.bot.set_my_commands(commands)

    # Starts loop worker for the queue
    asyncio.create_task(queue.start())


async def on_shutdown(dp: Dispatcher):
    """Execute function before Bot shut down polling."""

    log.info("Execute shutdown Bot functions...")

    # Close storage
    await dp.storage.close()
    await dp.storage.wait_closed()


def main():
    """Main app runner."""

    protected_handlers = ["answer_message", "report_confirmation"]
    throttling_middleware = ThrottlingMiddleware(
        protected_handlers,
        rate=config.THROTTLE_RATE,
    )

    storage = RedisStorage2(host=config.REDIS_HOST, port=config.REDIS_PORT)

    bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
    dp = Dispatcher(bot, storage=storage)
    dp.errors_handlers.once = True  # Fix errors rethrowing
    dp.middleware.setup(throttling_middleware)  # Throttling middleware

    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
    )


if __name__ == "__main__":
    main()
