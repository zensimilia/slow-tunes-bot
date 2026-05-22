from enum import IntEnum, auto
from typing import TYPE_CHECKING

from aiogram.enums.button_style import ButtonStyle
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.utils.emoji import get_btn_txt
from bot.utils.enums import Btn, FxAnalog, FxReverb

if TYPE_CHECKING:
    from aiogram.types import InlineKeyboardMarkup


class FxAnalogAction(IntEnum):
    LIST = auto()
    SELECT = auto()
    BACK = auto()


class FxAnalogCbd(CallbackData, prefix="analog"):
    action: FxAnalogAction
    value: FxAnalog | None = None

    def get_keyboard(self, current: FxAnalog | None = None) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()

        for item in FxAnalog:
            keyboard.row(
                InlineKeyboardButton(
                    text=get_btn_txt(item),
                    callback_data=FxAnalogCbd(action=FxAnalogAction.SELECT, value=item).pack(),
                    style=ButtonStyle.SUCCESS if item == current else None,
                ),
            )

        keyboard.row(
            InlineKeyboardButton(
                text=get_btn_txt(Btn.BACK),
                callback_data=FxAnalogCbd(action=FxAnalogAction.BACK).pack(),
                style=ButtonStyle.PRIMARY,
            ),
        )

        return keyboard.as_markup()


class FxReverbAction(IntEnum):
    LIST = auto()
    SELECT = auto()
    BACK = auto()


class FxReverbCbd(CallbackData, prefix="reverb"):
    action: FxReverbAction
    value: FxReverb | None = None

    def get_keyboard(self, current: FxReverb | None = None) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()

        for item in FxReverb:
            keyboard.row(
                InlineKeyboardButton(
                    text=get_btn_txt(item),
                    callback_data=FxReverbCbd(action=FxReverbAction.SELECT, value=item).pack(),
                    style=ButtonStyle.SUCCESS if item == current else None,
                ),
            )

        keyboard.row(
            InlineKeyboardButton(
                text=get_btn_txt(Btn.BACK),
                callback_data=FxAnalogCbd(action=FxAnalogAction.BACK).pack(),
                style=ButtonStyle.PRIMARY,
            ),
        )

        return keyboard.as_markup()
