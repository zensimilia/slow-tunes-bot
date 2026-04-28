from typing import TYPE_CHECKING, Any

from sqlalchemy import asc, desc, func, select, update

from db.exceptions import DoesNotExistError
from models.match import MatchModel
from schemas.match import MatchNew, MatchRead

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class MatchStore:
    model = MatchModel

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, match_new: MatchNew) -> MatchRead:
        new_match = MatchModel(**match_new.model_dump())
        self.session.add(new_match)
        await self.session.flush()
        await self.session.refresh(new_match)
        return MatchRead.model_validate(new_match)

    async def count(self, *, public_only: bool = False) -> int:
        query = select(func.count(MatchModel.pk))
        if public_only:
            query = query.where(
                self.model.is_private.is_(False),
                self.model.is_forbidden.is_(False),
            )
        return await self.session.scalar(query) or 0

    async def get(self, pk: int) -> MatchRead:
        if match := await self.session.get(MatchModel, pk):
            return MatchRead.model_validate(match)
        raise DoesNotExistError

    async def get_by(self, **kwargs: Any) -> MatchRead:
        query = select(self.model).filter_by(**kwargs).limit(1)
        if user := await self.session.scalar(query):
            return MatchRead.model_validate(user)
        raise DoesNotExistError

    async def get_by_original_id(self, original_id: str) -> MatchRead:
        return await self.get_by(original_id=original_id)

    async def get_random(self) -> MatchRead:
        query = select(self.model).order_by(func.random()).limit(1)
        if match := await self.session.scalar(query):
            return MatchRead.model_validate(match)
        raise DoesNotExistError

    async def get_list(self, limit: int = 10, offset: int = 0, *, sort_by_desc: bool = False) -> list[MatchRead]:
        direction = desc if sort_by_desc else asc
        query = select(self.model).order_by(direction(self.model.pk)).limit(limit).offset(offset)
        matches = list(await self.session.scalars(query))
        return [MatchRead.model_validate(m) for m in matches]

    async def update(self, pk: int, **values: Any) -> None:
        query = update(self.model).where(self.model.pk == pk).values(**values)
        await self.session.execute(query)
        await self.session.flush()
