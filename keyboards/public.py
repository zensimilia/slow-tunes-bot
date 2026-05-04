from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .buttons import admin_support_btn, app_license_btn, app_version_btn

if TYPE_CHECKING:
    from aiogram import Bot


def please_wait_button() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Please wait...", callback_data="pls_wit"))
    return keyboard.as_markup()


async def about_keyboard(bot: Bot) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    await admin_support_btn(keyboard, bot=bot)
    app_license_btn(keyboard)
    app_version_btn(keyboard)
    return keyboard.as_markup()


async def support_keyboard(bot: Bot) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    await admin_support_btn(keyboard, bot=bot)
    return keyboard.as_markup()
