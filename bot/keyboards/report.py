from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

report_cbd = CallbackData("report", "action", "idc")


def report_button(idc: str) -> InlineKeyboardMarkup:
    """Returns markup for Report button."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    "💩 Report!",
                    callback_data=report_cbd.new(
                        action="confirm",
                        idc=idc,
                    ),
                )
            ],
        ]
    )


def report_confirm_buttons(idc: str) -> InlineKeyboardMarkup:
    """Returns markup for report confirmation buttons."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    "YES",
                    callback_data=report_cbd.new(action="yes", idc=idc),
                ),
                InlineKeyboardButton(
                    "NO",
                    callback_data=report_cbd.new(action="no", idc=idc),
                ),
                InlineKeyboardButton(
                    "?",
                    callback_data=report_cbd.new(action="help", idc=idc),
                ),
            ],
        ]
    )
