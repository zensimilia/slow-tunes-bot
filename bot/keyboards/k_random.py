from aiogram.types import InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

random_cbd = CallbackData("random", "action", "idc")


def random_button(idc: str) -> InlineKeyboardButton:
    """Return inline keyboard button for random tune."""

    return InlineKeyboardButton(
        text="🎲 Next",
        callback_data=random_cbd.new(
            action="next",
            idc=idc,
        ),
    )  # pyright: ignore[reportArgumentType]
