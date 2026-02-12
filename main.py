from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.redis import RedisStorage2

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
    bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(bot, storage=storage)
    dp.errors_handlers.once = True  # Fix errors rethrowing
    dp.middleware.setup(throttling_middleware)  # Throttling middleware
    dp.filters_factory.bind(IsAdmin)

    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
    )


if __name__ == "__main__":
    main()
