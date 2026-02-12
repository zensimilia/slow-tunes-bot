from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

public_cbd = CallbackData("public", "action", "idc", "is_random")


def public_buttons(
    idc: str,
    is_random: bool,
    is_like: bool = False,
) -> InlineKeyboardMarkup:
    """Returns markup for like/dislike and report buttons."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💔 Dislike!" if is_like else "❤ Like!",
                    callback_data=public_cbd.new(
                        action="toggle_like",
                        idc=idc,
                        is_random=is_random,
                    ),
                ),  # pyright: ignore[reportArgumentType]
                InlineKeyboardButton(
                    text="💩 Report!",
                    callback_data=public_cbd.new(
                        action="report",
                        idc=idc,
                        is_random=is_random,
                    ),
                ),  # pyright: ignore[reportArgumentType]
            ]
        ]
    )


def report_confirm_buttons(idc: str, is_random: bool) -> InlineKeyboardMarkup:
    """Returns markup for report confirmation buttons."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❓",
                    callback_data=public_cbd.new(
                        action="report_help",
                        idc=idc,
                        is_random=is_random,
                    ),
                ),  # pyright: ignore[reportArgumentType]
                InlineKeyboardButton(
                    text="YES",
                    callback_data=public_cbd.new(
                        action="report_yes",
                        idc=idc,
                        is_random=is_random,
                    ),
                ),  # pyright: ignore[reportArgumentType]
                InlineKeyboardButton(
                    text="NO",
                    callback_data=public_cbd.new(
                        action="report_no",
                        idc=idc,
                        is_random=is_random,
                    ),
                ),  # pyright: ignore[reportArgumentType]
            ],
        ]
    )


def report_response_buttons(idc: str) -> InlineKeyboardMarkup:
    """Returns markup for report audio buttons sending to admin."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    "Accept",
                    callback_data=public_cbd.new(
                        action="report_accept",
                        idc=idc,
                        is_random=False,
                    ),
                ),  # pyright: ignore[reportArgumentType]
                InlineKeyboardButton(
                    "Decline",
                    callback_data=public_cbd.new(
                        action="report_decline",
                        idc=idc,
                        is_random=False,
                    ),
                ),  # pyright: ignore[reportArgumentType]
            ]
        ]
    )
