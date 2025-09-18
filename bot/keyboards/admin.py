from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

tunes_list_cbd = CallbackData("tunes_list", "page", "flag")


def tunes_pagging_buttons(curr_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Returns markup for tunes paginator buttons."""

    if total_pages == 1:
        return InlineKeyboardMarkup()

    markup = InlineKeyboardMarkup()

    if curr_page != 1:
        markup.insert(
            InlineKeyboardButton(
                "⬅",
                callback_data=tunes_list_cbd.new(page=curr_page - 1, flag="ok"),
            ),
        )

    markup.insert(
        InlineKeyboardButton(
            f"{curr_page}/{total_pages}",
            callback_data=tunes_list_cbd.new(page=curr_page, flag="ok"),
        )
    )

    if total_pages > 1 and curr_page != total_pages:
        markup.insert(
            InlineKeyboardButton(
                "➡",
                callback_data=tunes_list_cbd.new(
                    page=min(curr_page + 1, total_pages), flag="ok"
                ),
            ),
        )

    return markup
