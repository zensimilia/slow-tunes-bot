from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .cbd import ShareCbd


def get_share_keyboard(pk: int, is_private: bool, is_random: bool) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text="🤙 Publish" if is_private else "🔒 Unpublish",
            callback_data=ShareCbd(action="toggle_privacy", pk=pk, is_private=is_private, is_random=is_random).pack(),
        )
    )
    return keyboard.as_markup()
