from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

share_cbd = CallbackData("share", "action", "file_id")


def share_button(file_id: str) -> InlineKeyboardMarkup:
    """Returns markup of Share button."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    "🤙 Share?",
                    callback_data=share_cbd.new(
                        action="confirm",
                        file_id=file_id,
                    ),
                )
            ],
        ]
    )


def share_confirm_buttons(file_id: str) -> InlineKeyboardMarkup:
    """Returns markup for confirmation sharing buttons."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    "YES",
                    callback_data=share_cbd.new(
                        action="share",
                        file_id=file_id,
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "NO",
                    callback_data=share_cbd.new(
                        action="cancel",
                        file_id=file_id,
                    ),
                )
            ],
        ]
    )
