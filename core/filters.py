from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message


class IsAdmin(BaseFilter):
    def __init__(self, admin_ids: list[int]) -> None:
        self._admin_ids = admin_ids

    async def __call__(self, obj: Union[Message, CallbackQuery]) -> bool:
        if obj.from_user:
            return obj.from_user.id in self._admin_ids
        return False
