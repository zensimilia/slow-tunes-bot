import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, TypeVar

from sqlalchemy import Engine, event
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from models.base import BaseModel

from .exceptions import DataError, OperationalError

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable, Callable
    from sqlite3 import Connection

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Database:
    def __init__(self, url: str) -> None:
        self._url = url
        self.engine = create_async_engine(url=self._url)

        # SQLite PRAGMA fix
        @event.listens_for(Engine, "connect")
        def _set_sqlite_pragma(dbapi_connection: Connection, _connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
            logger.info("PRAGMA foreign_keys=ON")

        self._session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, Any]:
        async with self._session_factory() as session:
            try:
                yield session
            except IntegrityError as err:
                await session.rollback()
                logger.warning(err.orig)
                raise DataError(err._message) from err
            except SQLAlchemyError as err:
                await session.rollback()
                logger.exception("Database error")
                raise OperationalError(err._message) from err

    async def execute(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        async with self.get_session() as session:
            return await func(session, *args, **kwargs)

    async def close_all(self) -> None:
        await self.engine.dispose()
        logger.info("All database connections closed")

    async def create_tables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)
            logger.info("Tables for BaseModel created")
