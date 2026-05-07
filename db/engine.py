import logging
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

from models.base import BaseModel
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel, delete, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from db.exceptions import DoesNotExistError

from .exceptions import DataError, OperationalError

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable, Callable
    from sqlite3 import Connection

    from .engine import AsyncDatabaseProtocol

logger = logging.getLogger(__name__)

T = TypeVar("T")
M = TypeVar("M", bound=SQLModel)


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


class DbStorage:
    """
    Generic database storage repository implementing common CRUD operations.

    This class abstracts the interaction with SQLAlchemy models using an
    asynchronous database protocol, providing a high-level API for object
    persistence and retrieval.

    Attributes:
        db: An instance of `AsyncDatabaseProtocol` used for session management.
    """

    def __init__(self, db: AsyncDatabaseProtocol) -> None:
        """
        Initialize the storage with a database provider.

        Args:
            db: An object that provides managed database sessions.
        """
        self.db = db

    async def save(self, obj: M) -> M:
        """
        Persist a new or existing object to the database.

        Args:
            obj: The model instance to save.

        Returns:
            The saved and refreshed model instance with updated server-side state.
        """
        async with self.db.get_session() as s:
            s.add(obj)
            await s.commit()
            await s.refresh(obj)
            return obj

    async def create(self, obj: M) -> M:
        """
        Alias for the `save` method to create a new record.

        Args:
            obj: The model instance to create.

        Returns:
            The created model instance.
        """
        return await self.save(obj)

    async def delete(self, model: type[M], **filters: Any) -> None:
        """
        Delete records matching the specified filters.

        Args:
            model: The SQLAlchemy model class to delete from.
            **filters: Filter criteria for the delete query (e.g., id=1).
        """
        async with self.db.get_session() as s:
            query = delete(model).filter_by(**filters)
            await s.exec(query)

    async def get(self, model: type[M], pk: int) -> M | None:
        """
        Retrieve a single record by its primary key.

        Args:
            model: The SQLAlchemy model class.
            pk: Primary key value.

        Returns:
            The model instance if found, otherwise None.
        """
        async with self.db.get_session() as s:
            return await s.get(model, pk)

    async def get_by(self, model: type[M], **filters: Any) -> M | None:
        """
        Retrieve the first record matching the specified filters.

        Args:
            model: The SQLAlchemy model class.
            **filters: Filter criteria (e.g., email="user@example.com").

        Returns:
            The first matching model instance or None.
        """
        async with self.db.get_session() as s:
            query = select(model).filter_by(**filters).limit(1)
            return await s.scalar(query)

    async def get_many(self, model: type[M], *, limit: int, offset: int, **filters: Any) -> list[M]:
        """
        Retrieve a list of records with pagination and filtering.

        Args:
            model: The SQLAlchemy model class.
            limit: Maximum number of records to return.
            offset: Number of records to skip.
            **filters: Filter criteria for the selection.

        Returns:
            A list of matching model instances.
        """
        async with self.db.get_session() as s:
            query = select(model).offset(offset).limit(limit).filter_by(**filters)
            return list(await s.scalars(query))

    async def patch(self, model: type[M], pk: int, data: dict[str, Any]) -> M:
        async with self.db.get_session() as s:
            obj = await s.get(model, pk)
            if not obj:
                raise DoesNotExistError
            for key, value in data.items():
                setattr(obj, key, value)
            s.add(obj)
            await s.commit()
            await s.refresh(obj)
            return obj

    async def count(self, model: type[M], **filters: Any) -> int:
        """
        Count the number of records matching the specified filters.

        Args:
            model: The SQLAlchemy model class.
            **filters: Filter criteria for the count query.

        Returns:
            The total count of matching records.
        """
        async with self.db.get_session() as s:
            query = select(func.count()).select_from(model).filter_by(**filters)
            return await s.scalar(query) or 0
