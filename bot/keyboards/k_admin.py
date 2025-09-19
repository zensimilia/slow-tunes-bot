from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

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
            ),
        )

    markup.insert(
        InlineKeyboardButton(
            f"{curr_page}/{total_pages}",
            callback_data=tunes_list_cbd.new(
                page=curr_page, curr_page=curr_page, flag="ok"
            ),
        )
    )

    if total_pages > 1 and curr_page != total_pages:
        markup.insert(
            InlineKeyboardButton(
                "➡",
                callback_data=tunes_list_cbd.new(
                    page=min(curr_page + 1, total_pages), curr_page=curr_page, flag="ok"
                ),
            ),
        )

    return markup
