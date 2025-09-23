from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.utils.executor import start_webhook

from bot.config import config
from bot.middlewares.m_throttling import ThrottlingMiddleware
from bot.setup import on_shutdown, on_startup
from bot.utils.u_admin import IsAdmin
from bot.utils.u_logger import get_logger

LOG = get_logger()


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
    dp.filters_factory.bind(IsAdmin)

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
