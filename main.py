import asyncio

from core.bootstrap import setup_bot, setup_dispatcher
from core.logger import setup_logging


async def main():
    """Here we go again"""

    setup_logging()

    bot = setup_bot()
    dispatcher = setup_dispatcher()
    allowed_updates = dispatcher.resolve_used_update_types()

    try:
        await dispatcher.start_polling(bot, allowed_updates=allowed_updates)
    finally:
        await bot.session.close()  # just in case


if __name__ == "__main__":
    asyncio.run(main())
