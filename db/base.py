import logging
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel.ext.asyncio.session import AsyncSession

from models.base import BaseModel

from .exceptions import DataError, OperationalError

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable, Callable
    from sqlite3 import Connection

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AsyncDatabaseProtocol(Protocol):
    def get_session(self) -> AbstractAsyncContextManager[AsyncSession, Any]: ...
    async def execute(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T: ...


class Database:
    """
    Async database manager for SQLAlchemy with session lifecycle control.

    This class provides an interface for managing database connections,
    executing functions within session contexts, and handling SQLite-specific
    configurations like foreign key constraints.

    Attributes:
        engine (AsyncEngine): SQLAlchemy async engine instance.
    """

    def __init__(self, url: str, **kwargs: Any) -> None:
        """
        Initialize the database manager and setup the session factory.

        Args:
            url: Database connection URL (e.g., 'sqlite+aiosqlite:///db.sqlite3').
            **kwargs: Additional arguments passed to `async_sessionmaker`.

        Notes:
            `expire_on_commit` is set to False by default.
        """
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
        """
        Provide an async context manager for database sessions.

        Yields:
            An active `AsyncSession` instance.

        Raises:
            DataError: If an integrity constraint is violated.
            OperationalError: For general SQLAlchemy-related errors.
        """
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
        """
        Execute a function within a managed session context.

        The provided function must accept a `session` as its first argument.

        Args:
            func: An awaitable function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            The result of the executed function.

        Examples:
            ```python
            async def get_user(session, user_id):
                return await session.get(User, user_id)

            user = await db.execute(get_user, user_id=1)
            ```
        """
        async with self.get_session() as session:
            return await func(session, *args, **kwargs)

    async def close_all(self) -> None:
        """Dispose of the engine and close all active connections."""
        await self.engine.dispose()
        logger.info("All database connections closed")

    async def create_tables(self) -> None:
        """
        Initialize database tables based on the BaseModel metadata.

        Creates all tables defined in the metadata of the application's models.
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)
            logger.info("Tables for BaseModel created")
