from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

from .k_random import random_cbd

share_cbd = CallbackData("share", "action", "file_id", "is_private", "is_random")


def share_button(
    file_id: str, *, is_private: bool = True, is_random: bool = False
) -> InlineKeyboardMarkup:
    """Returns markup for Share button."""

    text = "🤙 Share?" if is_private else "🔒 Make private?"

    button = InlineKeyboardButton(
        text,
        callback_data=share_cbd.new(
            action="confirm",
            file_id=file_id,
            is_private=is_private,
            is_random=is_random,
        ),
    )  # pyright: ignore[reportArgumentType]

    markup = InlineKeyboardMarkup()
    markup.insert(button)

    if is_random:
        markup.row()
        markup.insert(
            InlineKeyboardButton(
                "🎲 Next",
                callback_data=random_cbd.new(
                    action="next",
                    idc=file_id,
                ),
            )  # pyright: ignore[reportArgumentType]
        )

    return markup


def share_confirm_buttons(
    file_id: str, *, is_private: bool, is_random: bool = False
) -> InlineKeyboardMarkup:
    """Returns markup for sharing confirmation buttons."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    "❓",
                    callback_data=share_cbd.new(
                        action="help",
                        file_id=file_id,
                        is_private=is_private,
                        is_random=is_random,
                    ),
                ),  # pyright: ignore[reportArgumentType]
                InlineKeyboardButton(
                    "YES",
                    callback_data=share_cbd.new(
                        action="yes",
                        file_id=file_id,
                        is_private=is_private,
                        is_random=is_random,
                    ),
                ),  # pyright: ignore[reportArgumentType]
                InlineKeyboardButton(
                    "NO",
                    callback_data=share_cbd.new(
                        action="no",
                        file_id=file_id,
                        is_private=is_private,
                        is_random=is_random,
                    ),
                ),  # pyright: ignore[reportArgumentType]
            ],
        ]
    )
