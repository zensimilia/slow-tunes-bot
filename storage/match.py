from typing import TYPE_CHECKING, Any

from sqlmodel import asc, desc, func, select

from models.match import Match, MatchNew

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


class MatchStore:
    model = Match

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, match_new: MatchNew) -> Match:
        match = self.model.model_validate(match_new)
        self.session.add(match)
        await self.session.flush()
        await self.session.refresh(match)
        return match

    async def count(self, *, public_only: bool = False) -> int:
        query = select(func.count()).select_from(self.model)
        if public_only:
            query = query.where(
                not self.model.is_private,
                not self.model.is_forbidden,
            )
        return await self.session.scalar(query) or 0

    async def get(self, pk: int) -> Match | None:
        return await self.session.get(self.model, pk)

    async def get_by(self, **kwargs: Any) -> Match | None:
        query = select(self.model).filter_by(**kwargs).limit(1)
        return await self.session.scalar(query)

    async def get_by_original_id(self, original_id: str) -> Match | None:
        return await self.get_by(original_id=original_id)

    async def get_list(self, *, limit: int = 10, offset: int = 0, sort_by_desc: bool = False) -> list[Match]:
        direction = desc if sort_by_desc else asc
        query = select(self.model).order_by(direction(self.model.pk)).offset(offset).limit(limit)
        return list(await self.session.scalars(query))
