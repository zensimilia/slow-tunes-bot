from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

share_cbd = CallbackData("share", "action", "file_id", "is_private")


def share_button(file_id: str, is_private: bool = True) -> InlineKeyboardMarkup:
    """Returns markup of Share button."""

    text = "🤙 Share?" if is_private else "🔒 Make private?"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text,
                    callback_data=share_cbd.new(
                        action="confirm",
                        file_id=file_id,
                        is_private=is_private,
                    ),
                )
            ],
        ]
    )


def share_confirm_buttons(
    file_id: str, is_private: bool
) -> InlineKeyboardMarkup:
    """Returns markup for confirmation sharing buttons."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    "YES",
                    callback_data=share_cbd.new(
                        action="yes",
                        file_id=file_id,
                        is_private=is_private,
                    ),
                ),
                InlineKeyboardButton(
                    "NO",
                    callback_data=share_cbd.new(
                        action="no",
                        file_id=file_id,
                        is_private=is_private,
                    ),
                ),
            ],
        ]
    )
