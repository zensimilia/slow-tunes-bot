from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

random_cbd = CallbackData("random", "action", "idc")


def random_buttons(idc: str, *, is_like: bool = False) -> InlineKeyboardMarkup:
    """Returns markup for /random audio buttons."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    "💔 Dislike!" if is_like else "❤ Like!",
                    callback_data=random_cbd.new(
                        action="toggle_like",
                        idc=idc,
                    ),
                ),
                InlineKeyboardButton(
                    "💩 Report!",
                    callback_data=random_cbd.new(
                        action="confirm",
                        idc=idc,
                    ),
                ),
            ]
        ]
    )


def report_confirm_buttons(idc: str) -> InlineKeyboardMarkup:
    """Returns markup for report confirmation buttons."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    "❓",
                    callback_data=random_cbd.new(action="help", idc=idc),
                ),
                InlineKeyboardButton(
                    "YES",
                    callback_data=random_cbd.new(action="yes", idc=idc),
                ),
                InlineKeyboardButton(
                    "NO",
                    callback_data=random_cbd.new(action="no", idc=idc),
                ),
            ],
        ]
    )
