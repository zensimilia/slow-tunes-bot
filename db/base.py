import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Awaitable, Callable, TypeVar

from sqlalchemy import Engine, event
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .exceptions import DataError, OperationalError
from .models import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Database:
    def __init__(self, url: str) -> None:
        self._url = url
        self.engine = create_async_engine(url=self._url)

        # SQLite PRAGMA fix
        @event.listens_for(Engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record):
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
                raise DataError from err
            except SQLAlchemyError as err:
                await session.rollback()
                logger.error(err)
                raise OperationalError from err

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
