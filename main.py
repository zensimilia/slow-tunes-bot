import asyncio
import sys

from bot.core.bootstrap import setup_bot, setup_dispatcher
from bot.core.logger import logger, setup_logging


async def main() -> None:
    """Ah s**t, here we go again."""

    setup_logging()

    bot = setup_bot()
    dispatcher = setup_dispatcher()
    allowed_updates = dispatcher.resolve_used_update_types()

    try:
        await dispatcher.start_polling(bot, allowed_updates=allowed_updates)
    except (KeyboardInterrupt, SystemExit) as exc:
        logger.critical(exc)
        sys.exit(getattr(exc, "code", 0))
    finally:
        logger.critical("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
