from enum import IntEnum, auto
from typing import TYPE_CHECKING

from aiogram.enums.button_style import ButtonStyle
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.services.ffmpeg import FxAnalog
from bot.utils.emoji import get_btn_txt
from bot.utils.enums import Btn

if TYPE_CHECKING:
    from aiogram.types import InlineKeyboardMarkup


class FxAnalogAction(IntEnum):
    LIST = auto()
    SELECT = auto()
    CLEAR = auto()
    BACK = auto()


class FxAnalogCbd(CallbackData, prefix="analog"):
    action: FxAnalogAction
    fx: FxAnalog | None = None

    def get_keyboard(self, current: FxAnalog | None = None) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()

        for fx in FxAnalog:
            keyboard.row(
                InlineKeyboardButton(
                    text=get_btn_txt(fx),
                    callback_data=FxAnalogCbd(action=FxAnalogAction.SELECT, fx=fx).pack(),
                    style=ButtonStyle.PRIMARY if fx == current else None,
                ),
            )

        keyboard.row(
            InlineKeyboardButton(
                text=get_btn_txt(Btn.BACK),
                callback_data=FxAnalogCbd(action=FxAnalogAction.BACK).pack(),
            ),
            InlineKeyboardButton(
                text=get_btn_txt(Btn.NONE),
                callback_data=FxAnalogCbd(action=FxAnalogAction.CLEAR).pack(),
                style=ButtonStyle.PRIMARY if not current else None,
            ),
        )

        return keyboard.as_markup()
