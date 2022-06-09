from aiogram import Dispatcher, types
from aiogram.utils.exceptions import Throttled

from bot.config import AppConfig
from bot.utils.logger import get_logger

config = AppConfig()
log = get_logger()


async def is_throttled(
    key: str, *, dispatcher: Dispatcher, message: types.Message
) -> bool:
    """Execute throttling manager.
    Returns True if limit has not exceeded otherwise returns False."""

    try:
        await dispatcher.throttle(key, rate=config.THROTTLE_RATE)
    except Throttled:
        log.debug("Throttled <User user_id=%s>", message.from_user.id)
        return True
    return False
