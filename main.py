import asyncio
import sys

from core.bootstrap import setup_bot, setup_dispatcher
from core.logger import logger, setup_logging


async def main() -> None:
    """Here we go again (c)."""

    setup_logging()

    bot = setup_bot()
    dispatcher = setup_dispatcher()
    allowed_updates = dispatcher.resolve_used_update_types()

    try:
        await dispatcher.start_polling(bot, allowed_updates=allowed_updates)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as err:  # noqa: BLE001
        logger.critical(err)
        sys.exit(1)
    finally:
        await bot.session.close()  # just in case


if __name__ == "__main__":
    asyncio.run(main())
