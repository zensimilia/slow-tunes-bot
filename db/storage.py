from typing import TYPE_CHECKING, Any, TypeVar

from sqlmodel import SQLModel, delete, func, select

from db.exceptions import DoesNotExistError

if TYPE_CHECKING:
    from .base import AsyncDatabaseProtocol

T = TypeVar("T", bound=SQLModel)


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

    async def save(self, obj: T) -> T:
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

    async def create(self, obj: T) -> T:
        """
        Alias for the `save` method to create a new record.

        Args:
            obj: The model instance to create.

        Returns:
            The created model instance.
        """
        return await self.save(obj)

    async def delete(self, model: type[T], **filters: Any) -> None:
        """
        Delete records matching the specified filters.

        Args:
            model: The SQLAlchemy model class to delete from.
            **filters: Filter criteria for the delete query (e.g., id=1).
        """
        async with self.db.get_session() as s:
            query = delete(model).filter_by(**filters)
            await s.exec(query)

    async def get(self, model: type[T], pk: int) -> T | None:
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

    async def get_by(self, model: type[T], **filters: Any) -> T | None:
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

    async def get_many(self, model: type[T], *, limit: int, offset: int, **filters: Any) -> list[T]:
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

    async def patch(self, model: type[T], pk: int, data: dict[str, Any]) -> T:
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

    async def count(self, model: type[T], **filters: Any) -> int:
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
