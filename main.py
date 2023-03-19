import asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.utils.executor import start_webhook

from bot import db
from bot.config import AppConfig
from bot.handlers import register_handlers
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.utils.logger import get_logger
from bot.utils.queue import Queue

log = get_logger()
config = AppConfig()


async def on_startup(dp: Dispatcher):
    """Execute function before Bot start polling."""

    log.info("Execute startup Bot functions...")
    db.execute_script("./schema.sql")

    # Set webhook
    if config.USE_WEBHOOK:
        await dp.bot.set_webhook(config.WEBHOOK_URL)

    register_handlers(dp)

    commands = [
        types.BotCommand("random", "get some slowed tune"),
        types.BotCommand("help", "if you stuck"),
        types.BotCommand("about", "bot info"),
    ]
    await dp.bot.set_my_commands(commands)

    # Starts loop worker for the queue
    dp.bot.data.update(queue=await Queue.create())
    asyncio.create_task(dp.bot.data["queue"].start())


async def on_shutdown(dp: Dispatcher):
    """Execute function before Bot shut down polling."""

    log.info("Execute shutdown Bot functions...")

    # Close Queue connection
    await dp.bot.data["queue"].stop()

    # Close storage
    await dp.storage.close()
    await dp.storage.wait_closed()

    # Clear list of bot commands
    await dp.bot.set_my_commands([])

    # Delete webhook
    if config.USE_WEBHOOK:
        await dp.bot.delete_webhook()


def main():
    """Main app runner."""

    protected_handlers = [
        "answer_message",
        "report_confirmation",
        "command_help",
        "command_start",
        "command_random",
        "command_about",
    ]
    throttling_middleware = ThrottlingMiddleware(
        protected_handlers,
        rate=config.THROTTLE_RATE,
    )

    storage = RedisStorage2(host=config.REDIS_HOST, port=config.REDIS_PORT)
    bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
    dp = Dispatcher(bot, storage=storage)
    dp.errors_handlers.once = True  # Fix errors rethrowing
    dp.middleware.setup(throttling_middleware)  # Throttling middleware

    if config.USE_WEBHOOK:
        start_webhook(
            dispatcher=dp,
            webhook_path=config.WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=config.APP_HOST,
            port=config.APP_PORT,
        )
    else:
        executor.start_polling(
            dp,
            skip_updates=True,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
        )


if __name__ == "__main__":
    main()
