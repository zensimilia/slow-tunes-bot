import json
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from bot.core.exceptions import MissingRequiredError
from bot.core.messages import PLS_SEND_START_CMD
from bot.utils.tg import answer_from_update
from db.models.user import User

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from redis.asyncio import Redis

    from db.storage.user import UserStore


USER_KEY = "user_cache"
USER_KEY_EXPIRE = 24 * 60 * 60  # 24 hours in seconds


class UserMiddleware(BaseMiddleware):
    """
    Middleware to load user data from the database and cache it in Redis.
    User object will be available in handlers as `user: GetUser` param.
    """

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
            user_obj = User.model_validate(user_data)
        else:
            user_store: UserStore | None = data.get("user_store")
            if not user_store:
                raise MissingRequiredError
            user_obj = await user_store.get_by(tg_id=user_tg_id)
            if not user_obj:
                return await answer_from_update(event_obj, PLS_SEND_START_CMD, is_reply=True)

        await self.__redis.set(user_key, user_obj.model_dump_json(), ex=self.__expire)

        data["user"] = user_obj
        return await handler(event, data)

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
