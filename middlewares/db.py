from typing import TYPE_CHECKING, Any, Protocol

from aiogram import BaseMiddleware

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from contextlib import AbstractAsyncContextManager

    from aiogram.types import TelegramObject
    from sqlalchemy.ext.asyncio import AsyncSession

from storage.match import MatchStore
from storage.user import UserStore


class AsyncDatabase(Protocol):
    def get_session(self) -> AbstractAsyncContextManager[AsyncSession, Any]: ...


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, db: AsyncDatabase) -> None:
        self.__db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with self.__db.get_session() as session:
            data["user_store"] = UserStore(session)
            data["match_store"] = MatchStore(session)

            return await handler(event, data)
