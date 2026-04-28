from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select

from db.exceptions import AlreadyExistsError, DoesNotExistError
from models.user import UserModel
from schemas.user import UserNew, UserRead

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class UserStore:
    model = UserModel

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_new: UserNew) -> UserRead:
        query = select(self.model).filter(self.model.tg_id == user_new.tg_id).limit(1)
        if await self.session.scalar(query):
            raise AlreadyExistsError

        user = self.model(**user_new.model_dump())
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return UserRead.model_validate(user)

    async def get(self, pk: int) -> UserRead:
        if user := await self.session.get(self.model, pk):
            return UserRead.model_validate(user)
        raise DoesNotExistError

    async def get_by(self, **kwargs: Any) -> UserRead:
        query = select(self.model).filter_by(**kwargs).limit(1)
        if user := await self.session.scalar(query):
            return UserRead.model_validate(user)
        raise DoesNotExistError

    async def count(self) -> int:
        query = select(func.count(self.model.pk))
        return await self.session.scalar(query) or 0
