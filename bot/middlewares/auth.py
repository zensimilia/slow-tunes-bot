import json
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from bot import messages as txt
from bot.core.exceptions import MissingRequiredError
from bot.utils.tg import answer_from_update
from db.models.user import User

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from redis.asyncio import Redis

    from db.repository.master import MasterStorage


USER_KEY = "user_cache"
USER_KEY_EXPIRE = 24 * 60 * 60  # 24 hours in seconds


class UserMiddleware(BaseMiddleware):
    """
    Middleware to load user data from the database and cache it in Redis.
    User object will be available in handlers as `user: GetUser` param.
    """

    def __init__(self, redis: Redis, expire: int = USER_KEY_EXPIRE) -> None:
        self._redis = redis
        self._expire = expire

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        event_obj = event.event

        if not isinstance(event_obj, (Message, CallbackQuery)):
            return await handler(event, data)

        if not event_obj.from_user:
            return await handler(event, data)

        if isinstance(event_obj, Message) and event_obj.text and event_obj.text.startswith("/start"):
            return await handler(event, data)

        user_tg_id = event_obj.from_user.id
        self._user_key = self.get_user_key(user_tg_id)

        user_obj = await self.get_cache()
        if not user_obj:
            store: MasterStorage | None = data.get("storage")
            if not store:
                raise MissingRequiredError
            user_obj = await store.user.get_by(tg_id=user_tg_id)
            if not user_obj:
                return await answer_from_update(event_obj, txt.PLS_SEND_START_CMD, is_reply=True)

        await self.set_cache(user_obj)
        data["user"] = user_obj
        return await handler(event, data)

    async def set_cache(self, user: User) -> None:
        await self._redis.set(self._user_key, user.model_dump_json(), ex=self._expire)

    async def get_cache(self) -> User | None:
        if cached_user := await self._redis.get(self._user_key):
            user_data = json.loads(cached_user)
            return User.model_validate(user_data)
        return None

    async def invalidate_cache(self) -> None:
        await self._redis.delete(self._user_key)

    @classmethod
    def get_user_key(cls, tg_id: int) -> str:
        """
        Returns a string by concatenating the constant `USER_KEY` with the provided `tg_id`.

        Args:
          tg_id: An integer representing the Telegram user ID.

        Returns:
            A result string.
        """
        return f"{USER_KEY}:{tg_id}"


async def invalidate_user_cache(dispatcher: Dispatcher) -> None:

    if user_middleware := next(
        (m for m in dispatcher.update.outer_middleware if isinstance(m, UserMiddleware)),
        None,
    ):
        await user_middleware.invalidate_cache()
