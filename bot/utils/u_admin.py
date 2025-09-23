from aiogram import Bot, types
from aiogram.dispatcher.filters import BoundFilter

from bot.config import config

from .u_logger import get_logger

LOG = get_logger()


class IsAdmin(BoundFilter):
    """Custom filter class to check if user is admin."""

    key = "is_admin"

    def __init__(self, is_admin: bool):
        self.is_admin = is_admin

    async def check(self, message: types.Message) -> bool:  # pylint: disable=all
        return message.from_user.id == config.ADMIN_ID


def get_tunes_list(data: list) -> str:
    """Generate table for tunes list."""

    str_list = "<b>Slowed tunes:</b>\n\n"

    for pk, _, _, user_id, is_private, is_forbidden in data:
        shared = "🔒" if bool(is_private) else "🤙"
        banned = "🔴" if bool(is_forbidden) else "🟢"
        str_list += f"{shared} {banned} /tune_{pk} by {user_id}\n"

    return str_list


async def get_username_by_id(bot: Bot, user_id: int):
    """Retrieves the username or user ID."""

    try:
        chat = await bot.get_chat(user_id)
        username = chat.username
        return f"@{username}" if username else f"#{user_id}"
    except Exception as e:
        LOG.warning("get_username_by_id: %s", e)
    return f"#{user_id}"
