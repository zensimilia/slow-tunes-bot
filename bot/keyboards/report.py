from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

report_response_cbd = CallbackData("report", "action", "idc")


def report_response_buttons(idc: str) -> InlineKeyboardMarkup:
    """Returns markup for report audio buttons sending to admin."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    "Accept",
                    callback_data=report_response_cbd.new(
                        action="accept",
                        idc=idc,
                    ),
                ),
                InlineKeyboardButton(
                    "Decline",
                    callback_data=report_response_cbd.new(
                        action="decline",
                        idc=idc,
                    ),
                ),
            ]
        ]
    )
