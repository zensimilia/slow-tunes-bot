from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

share_cbd = CallbackData("share", "action", "idc", "is_private", "is_random")


def share_button(
    idc: str, *, is_private: bool = True, is_random: bool
) -> InlineKeyboardMarkup:
    """Returns markup for Share button."""

    text = "🤙 Share?" if is_private else "🔒 Make private?"

    button = InlineKeyboardButton(
        text=text,
        callback_data=share_cbd.new(
            action="share_confirm",
            idc=idc,
            is_private=is_private,
            is_random=is_random,
        ),
    )  # pyright: ignore[reportArgumentType]

    markup = InlineKeyboardMarkup()
    markup.insert(button)

    return markup


def share_confirm_buttons(
    idc: str, *, is_private: bool, is_random: bool
) -> InlineKeyboardMarkup:
    """Returns markup for sharing confirmation buttons."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❓",
                    callback_data=share_cbd.new(
                        action="share_help",
                        idc=idc,
                        is_private=is_private,
                        is_random=is_random,
                    ),
                ),  # pyright: ignore[reportArgumentType]
                InlineKeyboardButton(
                    text="YES",
                    callback_data=share_cbd.new(
                        action="share_yes",
                        idc=idc,
                        is_private=is_private,
                        is_random=is_random,
                    ),
                ),  # pyright: ignore[reportArgumentType]
                InlineKeyboardButton(
                    text="NO",
                    callback_data=share_cbd.new(
                        action="share_no",
                        idc=idc,
                        is_private=is_private,
                        is_random=is_random,
                    ),
                ),  # pyright: ignore[reportArgumentType]
            ],
        ]
    )
