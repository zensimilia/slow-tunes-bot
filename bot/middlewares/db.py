from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types import TelegramObject

    from db.engine import AsyncDatabaseProtocol

from db.engine import DbStorage
from db.repository.match import MatchStore
from db.repository.user import UserStore


class DbSessionMiddleware(BaseMiddleware):
    """A middleware component for managing database sessions in a aiogram bot application."""

    def __init__(self, db: AsyncDatabaseProtocol) -> None:
        self._db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["db"] = self._db
        async with self._db.get_session() as session:
            storage = DbStorage(session)
            data["user_store"] = UserStore(storage)
            data["match_store"] = MatchStore(storage)
            return await handler(event, data)
