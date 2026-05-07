from typing import TYPE_CHECKING, Any

from db.models.like import Like, LikeNew

if TYPE_CHECKING:
    from db.storage.proto import StorageProtocol


class LikeStore:
    model: type[Like] = Like

    def __init__(self, storage: StorageProtocol[Like]) -> None:
        self.storage = storage

    async def create(self, like_new: LikeNew) -> Like:
        like = self.model.model_validate(like_new)
        return await self.storage.create(like)

    async def count(self, **kwargs: Any) -> int:
        return await self.storage.count(self.model, **kwargs) or 0

    async def get(self, pk: int) -> Like | None:
        return await self.storage.get(self.model, pk)

    async def get_by(self, **kwargs: Any) -> Like | None:
        return await self.storage.get_by(self.model, **kwargs)

    async def delete(self, pk: int) -> None:
        return await self.storage.delete(self.model, pk=pk)

    async def delete_where(self, **kwargs: Any) -> None:
        return await self.storage.delete(self.model, **kwargs)
