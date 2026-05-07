from typing import TYPE_CHECKING, Any

from db.models.match import Match, MatchNew

if TYPE_CHECKING:
    from db.storage import StorageProtocol


class MatchStore:
    model: type[Match] = Match

    def __init__(self, storage: StorageProtocol[Match]) -> None:
        self.storage = storage

    async def get_or_create(self, match_new: MatchNew) -> Match:
        if match_exist := await self.get_by_original_id(match_new.original_id):
            return match_exist
        return await self.create(match_new)

    async def create(self, match_new: MatchNew) -> Match:
        match = self.model.model_validate(match_new.model_dump())
        return await self.storage.create(match)

    async def count(self, *, public_only: bool = False) -> int:
        filters = {}
        if public_only:
            filters = {"is_private": False, "is_forbidden": False}
        return await self.storage.count(self.model, **filters)

    async def get(self, pk: int) -> Match | None:
        return await self.storage.get(self.model, pk)

    async def get_by(self, **kwargs: Any) -> Match | None:
        return await self.storage.get_by(self.model, **kwargs)

    async def get_by_original_id(self, original_id: str) -> Match | None:
        return await self.get_by(original_id=original_id)

    async def get_list(self, *, limit: int = 10, offset: int = 0, sort_by_desc: bool = False) -> list[Match]:
        order = "desc" if sort_by_desc else "asc"
        return list(await self.storage.get_many(self.model, limit=limit, offset=offset, order=order))
