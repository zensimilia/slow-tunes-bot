from typing import TYPE_CHECKING

from bot.utils.enums import Btn, FxAnalog, FxFilter, FxReverb

if TYPE_CHECKING:
    from enum import Enum


EMOJIS = {
    FxAnalog.VINYL: "📀",
    FxAnalog.TAPE: "📽️",
    FxAnalog.HISS: "📼",
    FxReverb.NORMAL: "🏠",
    FxReverb.EXTREME: "🏟",
    FxFilter.LOFI: "🎧",
    FxFilter.RADIO: "📻",
    FxFilter.TELEPHONE: "☎",
    Btn.BACK: "⏮",
    Btn.NONE: "❌",
}


def get_emoji(enum: Enum) -> str:
    return EMOJIS.get(enum, "🔵")


def get_btn_txt(enum: Enum) -> str:
    return f"{get_emoji(enum)} {str(enum).capitalize()}"
