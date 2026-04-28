from typing import TYPE_CHECKING

from aiogram.filters import BaseFilter

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery, Message


class IsAdmin(BaseFilter):
    def __init__(self, admin_ids: list[int]) -> None:
        self._admin_ids = admin_ids

    async def __call__(self, obj: Message | CallbackQuery) -> bool:
        if obj.from_user:
            return obj.from_user.id in self._admin_ids
        return False
