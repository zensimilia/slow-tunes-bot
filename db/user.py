from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.exceptions import DoesNotExist

from .models import User
from .schemas import GetUser, NewUser


async def create_user(session: AsyncSession, user_schema: NewUser) -> GetUser:
    query = select(User).filter_by(tg_id=user_schema.tg_id).limit(1)
    if existing := await session.scalar(query):
        return GetUser.model_validate(existing)

    new_user = User(**user_schema.model_dump())
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return GetUser.model_validate(new_user)


async def get_user_by_pk(session: AsyncSession, pk: int) -> GetUser:
    query = select(User).filter_by(pk=pk).limit(1)
    if user := await session.scalar(query):
        return GetUser.model_validate(user)
    raise DoesNotExist(f"User with pk={pk} doesn't exist")


async def get_user_by_tg_id(session: AsyncSession, tg_id: int) -> GetUser:
    query = select(User).filter_by(tg_id=tg_id).limit(1)
    if user := await session.scalar(query):
        return GetUser.model_validate(user)
    raise DoesNotExist(f"User with tg_id={tg_id} doesn't exist")


async def get_users_count(session: AsyncSession) -> int:
    query = select(func.count(User.pk))
    return await session.scalar(query) or 0
