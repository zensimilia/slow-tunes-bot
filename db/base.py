import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, TypeVar

from sqlalchemy import event
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
    def __init__(self, url: str, **kwargs: Any) -> None:
        self._url = url
        self.engine = create_async_engine(url=self._url)

        session_opts: dict[str, Any] = {"expire_on_commit": False}
        session_opts.update(**kwargs)

        self._session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            **session_opts,
        )

        # SQLite PRAGMA fix
        @event.listens_for(self.engine.sync_engine, "connect")
        def set_sqlite_pragma(connection: Connection, _record: Any) -> None:
            sql = "PRAGMA foreign_keys=ON"
            cursor = connection.cursor()
            cursor.execute(sql)
            cursor.close()
            logger.info(sql)

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
