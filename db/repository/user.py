from typing import TYPE_CHECKING, Any

from db.models.user import User, UserNew

if TYPE_CHECKING:
    from db.storage import StorageProtocol

DEFAULT_USERNAME = "Private Person"


class UserStore:
    model: type[User] = User

    def __init__(self, storage: StorageProtocol[User]) -> None:
        self.storage = storage

    async def create(self, user_new: UserNew) -> User:
        if user_exist := await self.storage.get_by(self.model, tg_id=user_new.tg_id):
            user_exist.username = user_new.username or DEFAULT_USERNAME
            return await self.storage.save(user_exist)

        user = self.model.model_validate(user_new)
        return await self.storage.create(user)

    async def get(self, pk: int) -> User | None:
        return await self.storage.get(self.model, pk)

    async def get_by(self, **kwargs: Any) -> User | None:
        return await self.storage.get_by(self.model, **kwargs)

    async def count(self) -> int:
        return await self.storage.count(self.model) or 0
