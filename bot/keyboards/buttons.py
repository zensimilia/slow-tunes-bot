from typing import TYPE_CHECKING

from aiogram import Bot, types

from bot.core.config import config
from bot.utils import tg, version

if TYPE_CHECKING:
    from aiogram.utils.keyboard import InlineKeyboardBuilder


async def admin_support_btn(keyboard: InlineKeyboardBuilder, *, bot: Bot) -> None:
    admin_url = await tg.get_user_url(bot, config.BOT_ADMIN_ID)
    keyboard.row(types.InlineKeyboardButton(text="👨‍💻 Admin & Support", url=admin_url))


def app_version_btn(keyboard: InlineKeyboardBuilder) -> None:
    app_version = version.get_app_version()
    keyboard.row(types.InlineKeyboardButton(text=f"💾 Version {app_version}", url=config.SOURCE_URL))


def app_license_btn(keyboard: InlineKeyboardBuilder, *, url: str | None = None) -> None:
    keyboard.row(types.InlineKeyboardButton(text="📜 License", url=url or config.LICENSE_URL))
