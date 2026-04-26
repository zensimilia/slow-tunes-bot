import json
from collections.abc import Awaitable
from typing import Any, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update
from redis.asyncio import Redis

from core.messages import PLS_SEND_START_CMD
from db.base import Database
from db.exceptions import DoesNotExist
from db.schemas import GetUser
from db.user import get_user_by_tg_id

USER_KEY_EXPIRE = 24 * 60 * 60  # 24 hours in seconds


class UserMiddleware(BaseMiddleware):
    """Middleware to load user data from the database and cache it in Redis.
    User object will be available in handlers as `user: GetUser` param."""

    def __init__(self, db: Database, redis: Redis, expire: int = USER_KEY_EXPIRE) -> None:
        self.__db = db
        self.__redis = redis
        self.__expire = expire

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        event_obj = event.event

        if not isinstance(event_obj, (Message, CallbackQuery)):
            return await handler(event, data)

        if not event_obj.from_user:
            return await handler(event, data)

        if isinstance(event_obj, Message) and event_obj.text:
            if event_obj.text.startswith("/start"):
                return await handler(event, data)

        user_id = event_obj.from_user.id
        user_key = self.get_user_key(user_id)
        cached_user = await self.__redis.get(user_key)

        if cached_user:
            user_data = json.loads(cached_user)
            user_obj = GetUser.model_validate(user_data)
        else:
            try:
                user_obj = await self.__db.execute(get_user_by_tg_id, user_id)
            except DoesNotExist:
                if isinstance(event_obj, Message):
                    return await event_obj.answer(PLS_SEND_START_CMD)
                elif isinstance(event_obj, CallbackQuery):
                    return await event_obj.answer(PLS_SEND_START_CMD, show_alert=True)

            await self.__redis.set(user_key, user_obj.model_dump_json(), ex=self.__expire)

        data["user"] = user_obj
        await handler(event, data)

    @classmethod
    def get_user_key(cls, tg_id: int) -> str:
        return f"user_cache:{tg_id}"
