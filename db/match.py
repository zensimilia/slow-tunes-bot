from sqlalchemy import asc, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.exceptions import DoesNotExist, NotFound
from db.schemas import GetMatch, NewMatch

from .models import Match


async def create_match(session: AsyncSession, match_schema: NewMatch) -> GetMatch:
    new_match = Match(**match_schema.model_dump())
    session.add(new_match)
    await session.commit()
    await session.refresh(new_match)
    return GetMatch.model_validate(new_match)


async def get_matches_count(session: AsyncSession, public_only: bool = False) -> int:
    query = select(func.count(Match.pk))
    if public_only:
        query = query.where(
            Match.private.is_(False),
            Match.forbidden.is_(False),
        )
    return await session.scalar(query) or 0


async def get_match(session: AsyncSession, pk: int) -> GetMatch:
    if match := await session.get(Match, pk):
        return GetMatch.model_validate(match)
    raise DoesNotExist(f"Match with pk={pk} doesn't exist")


async def get_match_by_original_id(session: AsyncSession, original_id: str) -> GetMatch:
    query = select(Match).where(Match.original_id == original_id)
    if match := await session.scalar(query):
        return GetMatch.model_validate(match)
    raise DoesNotExist(f"Match with original_id={original_id} doesn't exist")


async def get_random_match(session: AsyncSession) -> GetMatch:
    query = select(Match).order_by(func.random()).limit(1)
    if match := await session.scalar(query):
        return GetMatch.model_validate(match)
    raise NotFound("No matches found")


async def get_match_list(
    session: AsyncSession,
    limit: int = 10,
    offset: int = 0,
    sort_by_desc: bool = False,
) -> list[GetMatch]:
    direction = desc if sort_by_desc else asc
    query = select(Match).order_by(direction(Match.pk)).limit(limit).offset(offset)
    matches = list(await session.scalars(query))
    return [GetMatch.model_validate(m) for m in matches]


async def update_match_status(session: AsyncSession, pk: int, **values: bool) -> None:
    query = update(Match).where(Match.pk == pk).values(**values)
    await session.execute(query)
    await session.commit()
