import json
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from core.exceptions import MissingRequiredError
from core.messages import PLS_SEND_START_CMD
from db.exceptions import DoesNotExistError
from schemas.user import UserRead
from utils.tg import answer_from_update

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from redis.asyncio import Redis


USER_KEY = "user_cache"
USER_KEY_EXPIRE = 24 * 60 * 60  # 24 hours in seconds


class UserMiddleware(BaseMiddleware):
    """Middleware to load user data from the database and cache it in Redis.
    User object will be available in handlers as `user: GetUser` param."""

    def __init__(self, redis: Redis, expire: int = USER_KEY_EXPIRE) -> None:
        self.__redis = redis
        self.__expire = expire

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
        user_key = self.get_user_key(user_tg_id)
        cached_user = await self.__redis.get(user_key)

        if cached_user:
            user_data = json.loads(cached_user)
            user_obj = UserRead.model_validate(user_data)
        else:
            try:
                user_store = data.get("user_store")
                if not user_store:
                    raise MissingRequiredError
                user_obj = await user_store.get_by(tg_id=user_tg_id)
            except DoesNotExistError:
                return await answer_from_update(event_obj, PLS_SEND_START_CMD, is_reply=True)

            await self.__redis.set(user_key, user_obj.model_dump_json(), ex=self.__expire)

        data["user"] = user_obj
        return await handler(event, data)

    @classmethod
    def get_user_key(cls, tg_id: int) -> str:
        return f"{USER_KEY}:{tg_id}"
