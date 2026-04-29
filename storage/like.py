from typing import TYPE_CHECKING, Any

from sqlmodel import delete, func, select

from models.like import Like, LikeNew

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


class LikeStore:
    model = Like

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, like_new: LikeNew) -> Like:
        like = self.model.model_validate(like_new)
        self.session.add(like)
        await self.session.flush()
        await self.session.refresh(like)
        return like

    async def count(self, **kwargs: Any) -> int:
        query = select(func.count()).select_from(self.model).filter_by(**kwargs)
        return await self.session.scalar(query) or 0

    async def get(self, pk: int) -> Like | None:
        return await self.session.get(self.model, pk)

    async def get_by(self, **kwargs: Any) -> Like | None:
        query = select(self.model).filter_by(**kwargs).limit(1)
        return await self.session.scalar(query)

    async def delete(self, pk: int) -> None:
        if like := await self.get(pk):
            await self.session.delete(like)
            await self.session.flush()

    async def delete_where(self, **kwargs: Any) -> None:
        query = delete(self.model).where(**kwargs)
        await self.session.exec(query)
