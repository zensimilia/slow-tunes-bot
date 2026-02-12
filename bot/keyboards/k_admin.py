from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

from .k_random import random_cbd
from .k_share import share_button

tunes_list_cbd = CallbackData("tunes_list", "page", "curr_page", "flag")


def tunes_pagging_buttons(curr_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Returns markup for tunes paginator buttons."""

    markup = InlineKeyboardMarkup()

    if total_pages == 1:
        return markup

    if curr_page != 1:
        markup.insert(
            InlineKeyboardButton(
                "⬅",
                callback_data=tunes_list_cbd.new(
                    page=curr_page - 1, curr_page=curr_page, flag="ok"
                ),
            ),  # pyright: ignore[reportArgumentType]
        )

    markup.insert(
        InlineKeyboardButton(
            f"{curr_page}/{total_pages}",
            callback_data=tunes_list_cbd.new(
                page=curr_page, curr_page=curr_page, flag="ok"
            ),
        ),  # pyright: ignore[reportArgumentType]
    )

    if total_pages > 1 and curr_page != total_pages:
        markup.insert(
            InlineKeyboardButton(
                "➡",
                callback_data=tunes_list_cbd.new(
                    page=min(curr_page + 1, total_pages), curr_page=curr_page, flag="ok"
                ),
            ),  # pyright: ignore[reportArgumentType]
        )

    return markup


def tune_buttons(
    idc: str,
    file_id: str,
    is_private: bool,
    is_own: bool,
    is_liked: bool,
) -> InlineKeyboardMarkup:
    """Returns markup for single tune."""

    if is_own:
        markup = share_button(file_id, is_private=is_private, is_random=False)
    else:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        "💔 Dislike!" if is_liked else "❤ Like!",
                        callback_data=random_cbd.new(
                            action="toggle_like",
                            idc=idc,
                        ),
                    ),  # pyright: ignore[reportArgumentType]
                    InlineKeyboardButton(
                        "💩 Report!",
                        callback_data=random_cbd.new(
                            action="confirm",
                            idc=idc,
                        ),
                    ),  # pyright: ignore[reportArgumentType]
                ]
            ]
        )

    return markup
