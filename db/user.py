from sqlalchemy import func, select

from db.exceptions import DoesNotExist

from .base import Database
from .models import User
from .schemas import GetUser, NewUser


async def create_user(db: Database, user_schema: NewUser) -> GetUser:
    async with db.get_session() as session:
        query = select(User).filter_by(tg_id=user_schema.tg_id).limit(1)
        if existing := await session.scalar(query):
            return GetUser.model_validate(existing)

        new_user = User(**user_schema.model_dump())
        session.add(new_user)
        await session.flush()
        await session.refresh(new_user)
        return GetUser.model_validate(new_user)


async def get_user(db: Database, pk: int) -> GetUser:
    async with db.get_session() as session:
        query = select(User).filter_by(pk=pk).limit(1)
        if user := await session.scalar(query):
            return GetUser.model_validate(user)
    raise DoesNotExist(f"User with pk={pk} doesn't exist")


async def get_users_count(db: Database) -> int:
    async with db.get_session() as session:
        query = select(func.count(User.pk))
        return await session.scalar(query) or 0
