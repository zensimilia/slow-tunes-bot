from aiogram import Dispatcher, executor

from bot.dispatcher import create_dispatcher
from bot.handlers import register_handlers


async def on_startup(_dp: Dispatcher):
    """Execute function before Bot start polling."""


async def on_shutdown(_dp: Dispatcher):
    """Execute function before Bot shut down polling."""


def main():
    """Main app function."""

    dp = create_dispatcher()

    register_handlers(dp)

    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
    )


if __name__ == '__main__':
    main()
