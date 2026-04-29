from typing import TYPE_CHECKING, Any

from sqlmodel import func, select

from models.user import User, UserNew

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

DEFAULT_USERNAME = "Private Person"


class UserStore:
    model = User

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_new: UserNew) -> User:
        user_get_query = select(self.model).where(self.model.tg_id == user_new.tg_id).limit(1)
        if user_exist := await self.session.scalar(user_get_query):
            user_exist.username = user_new.username or DEFAULT_USERNAME
            await self.session.flush()
            return user_exist

        user = self.model.model_validate(user_new)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get(self, pk: int) -> User | None:
        return await self.session.get(self.model, pk)

    async def get_by(self, **kwargs: Any) -> User | None:
        user_get_query = select(self.model).filter_by(**kwargs).limit(1)
        return await self.session.scalar(user_get_query)

    async def count(self) -> int:
        query = select(func.count()).select_from(self.model)
        return await self.session.scalar(query) or 0
