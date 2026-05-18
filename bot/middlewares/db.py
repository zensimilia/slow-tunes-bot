from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types import TelegramObject

    from bot.core.database import AsyncDatabaseProtocol

from db.repository.master import MasterStorage
from db.sqlite import SqliteStorage


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
            storage = SqliteStorage(session)
            data["storage"] = MasterStorage(storage)
            return await handler(event, data)
