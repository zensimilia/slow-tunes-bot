from typing import TYPE_CHECKING

from bot.utils.enums import Btn, FxAnalog

if TYPE_CHECKING:
    from enum import Enum


def get_emoji(obj: Enum) -> str:
    match obj:
        case FxAnalog.VINYL:
            return "📀"
        case FxAnalog.TAPE:
            return "📽️"
        case FxAnalog.HISS:
            return "📼"
        case Btn.BACK:
            return "⏮"
        case Btn.NONE:
            return "❌"
        case _:
            return "🔵"


def get_btn_txt(obj: Enum) -> str:
    return f"{get_emoji(obj)} {str(obj).capitalize()}"
