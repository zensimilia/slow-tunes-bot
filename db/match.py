from sqlalchemy import asc, desc, func, select, update

from db.exceptions import DoesNotExist, NotFound
from db.schemas import GetMatch

from .base import Database
from .models import Match


async def get_matches_count(db: Database, public_only: bool = False) -> int:
    async with db.get_session() as session:
        query = select(func.count(Match.pk))
        if public_only:
            query = query.where(
                Match.private.is_(False),
                Match.forbidden.is_(False),
            )
        return await session.scalar(query) or 0


async def get_match(db: Database, pk: int) -> GetMatch:
    async with db.get_session() as session:
        if match := await session.get(Match, pk):
            return GetMatch.model_validate(match)
    raise DoesNotExist(f"Match with pk={pk} doesn't exist")


async def get_random_match(db: Database) -> GetMatch:
    async with db.get_session() as session:
        query = select(Match).order_by(func.random()).limit(1)
        if match := await session.scalar(query):
            return GetMatch.model_validate(match)
    raise NotFound("No matches found")


async def get_match_list(
    db: Database,
    limit: int = 10,
    offset: int = 0,
    sort_by_desc: bool = False,
) -> list[GetMatch]:
    direction = desc if sort_by_desc else asc
    async with db.get_session() as session:
        query = select(Match).order_by(direction(Match.pk)).limit(limit).offset(offset)
        matches = list(await session.scalars(query))
        return [GetMatch.model_validate(m) for m in matches]


async def update_private(db: Database, pk: int, is_private: bool = True) -> None:
    async with db.get_session() as session:
        query = update(Match).where(Match.pk == pk).values(private=is_private)
        await session.execute(query)


async def update_forbidden(db: Database, pk: int, is_forbidden: bool = True) -> None:
    async with db.get_session() as session:
        query = update(Match).where(Match.pk == pk).values(forbidden=is_forbidden)
        await session.execute(query)
