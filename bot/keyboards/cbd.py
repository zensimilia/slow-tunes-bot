from enum import IntEnum, auto
from typing import TYPE_CHECKING

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

if TYPE_CHECKING:
    from aiogram.types import InlineKeyboardMarkup


class MatchAction(IntEnum):
    NONE = auto()
    SHARE = auto()
    SHARE_HELP = auto()
    SHARE_YES = auto()
    SHARE_NO = auto()
    REPORT = auto()
    REPORT_HELP = auto()
    REPORT_YES = auto()
    REPORT_NO = auto()
    LIKE_TOGGLE = auto()
    NEXT = auto()


class MatchCbd(CallbackData, prefix="match"):
    action: MatchAction
    pk: int

    def get_keyboard(
        self,
        *,
        is_owner: bool,
        is_private: bool,
        is_liked: bool = False,
        is_random: bool = False,
    ) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()

        if self.action == MatchAction.NONE:
            if is_owner:
                keyboard.row(
                    InlineKeyboardButton(
                        text="🤙 Publish" if is_private else "🔒 Unpublish",
                        callback_data=MatchCbd(action=MatchAction.SHARE, pk=self.pk).pack(),
                    ),
                )
            else:
                keyboard.row(
                    InlineKeyboardButton(
                        text="💔 Dislike!" if is_liked else "❤ Like!",
                        callback_data=MatchCbd(action=MatchAction.LIKE_TOGGLE, pk=self.pk).pack(),
                    ),
                    InlineKeyboardButton(
                        text="💩 Report!",
                        callback_data=MatchCbd(action=MatchAction.REPORT, pk=self.pk).pack(),
                    ),
                )
        if self.action == MatchAction.SHARE:
            keyboard.row(
                InlineKeyboardButton(
                    text="YES",
                    callback_data=MatchCbd(action=MatchAction.SHARE_YES, pk=self.pk).pack(),
                ),
                InlineKeyboardButton(
                    text="HELP",
                    callback_data=MatchCbd(action=MatchAction.SHARE_HELP, pk=self.pk).pack(),
                ),
                InlineKeyboardButton(
                    text="NO",
                    callback_data=MatchCbd(action=MatchAction.SHARE_NO, pk=self.pk).pack(),
                ),
            )
        if self.action == MatchAction.REPORT:
            keyboard.row(
                InlineKeyboardButton(
                    text="YES",
                    callback_data=MatchCbd(action=MatchAction.REPORT_YES, pk=self.pk).pack(),
                ),
                InlineKeyboardButton(
                    text="HELP",
                    callback_data=MatchCbd(action=MatchAction.REPORT_HELP, pk=self.pk).pack(),
                ),
                InlineKeyboardButton(
                    text="NO",
                    callback_data=MatchCbd(action=MatchAction.REPORT_NO, pk=self.pk).pack(),
                ),
            )
        if is_random:
            keyboard.row(
                InlineKeyboardButton(
                    text="🎲 Next",
                    callback_data=MatchCbd(action=MatchAction.NEXT, pk=self.pk).pack(),
                ),
            )

        return keyboard.as_markup()
