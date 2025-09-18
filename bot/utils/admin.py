from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from bot.config import config


class IsAdmin(BoundFilter):
    """Custom filter class to check if user is admin."""

    key = "is_admin"

    def __init__(self, is_admin: bool):
        self.is_admin = is_admin

    async def check(self, message: types.Message) -> bool:
        return message.from_user.id == config.ADMIN_ID


def get_tunes_list(data: list) -> str:
    """Generate table for tunes list."""

    table = ""

    for pk, _, _, user_id, is_private, is_forbidden in data:
        shared = "🔒" if bool(is_private) else "🤙"
        banned = "💩" if bool(is_forbidden) else "🟢"
        table += f"{pk}. {shared} {banned} /tune_{pk} by {user_id}\n"

    return str(table)
