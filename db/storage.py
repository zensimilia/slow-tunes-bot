from typing import TYPE_CHECKING, Any, TypeVar

from sqlmodel import SQLModel, delete, func, select

if TYPE_CHECKING:
    from .base import AsyncDatabaseProtocol

T = TypeVar("T", bound=SQLModel)


class DbStorage:
    def __init__(self, db: AsyncDatabaseProtocol) -> None:
        self.db = db

    async def save(self, obj: T) -> T:
        async with self.db.get_session() as s:
            s.add(obj)
            await s.commit()
            await s.refresh(obj)
            return obj

    async def create(self, obj: T) -> T:
        return await self.save(obj)

    async def delete(self, model: type[T], **filters: Any) -> None:
        async with self.db.get_session() as s:
            query = delete(model).filter_by(**filters)
            await s.exec(query)

    async def get(self, model: type[T], pk: int) -> T | None:
        async with self.db.get_session() as s:
            return await s.get(model, pk)

    async def get_by(self, model: type[T], **filters: Any) -> T | None:
        async with self.db.get_session() as s:
            query = select(model).filter_by(**filters).limit(1)
            return await s.scalar(query)

    async def get_many(self, model: type[T], *, limit: int, offset: int, **filters: Any) -> list[T]:
        async with self.db.get_session() as s:
            query = select(model).offset(offset).limit(limit).filter_by(**filters)
            return list(await s.scalars(query))

    async def patch(self, obj: SQLModel, data: dict[str, Any]) -> None:
        async with self.db.get_session() as s:
            for key, value in data.items():
                setattr(obj, key, value)
            s.add(obj)
            await s.commit()
            return await s.refresh(obj)

    async def count(self, model: type[T], **filters: Any) -> int:
        async with self.db.get_session() as s:
            query = select(func.count()).select_from(model).filter_by(**filters)
            return await s.scalar(query) or 0
