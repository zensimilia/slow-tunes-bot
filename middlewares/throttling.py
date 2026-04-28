from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from loguru import logger

from core.messages import THROTTLING_TEXT
from utils.tg import answer_from_update

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types import CallbackQuery, Message, TelegramObject
    from redis.asyncio import Redis


class RateLimitMiddleware(BaseMiddleware):
    """
    Middleware for handling request rate limiting (throttling) using Redis.

    This middleware restricts the frequency of requests from a single user based on
    specific flags set on handlers. It prevents spam and excessive load on "heavy" tasks.

    Usage:
        1. Register the middleware in your Dispatcher:
           > redis = Redis()
           > dp.message.middleware(RateLimitMiddleware(redis))
           > dp.callback_query.middleware(RateLimitMiddleware(redis))

        2. Apply flags to your handlers:
           > @router.message(CommandStart())
           > @flags.rate_limit(rate=5, key="start_command")
           > async def cmd_start(message: Message): ...

           OR

           > rate_limit = {"rate_limit": {"rate": 3, "key": "start_command"}}
           > router.message.register(cmd_start, CommandStart(), flags=rate_limit)

    Configuration Flags:
        - rate (int): The cooldown period in seconds (default: 1).
        - key (str): A unique identifier for the limit scope (default: "common").
          Handlers sharing the same key will share the same rate limit.

    Logic:
        - If a user sends a request within the cooldown period, the request is ignored.
        - On the first attempt to exceed the limit, the user receives a notification.

    :param redis: An instance of `redis.asyncio.Redis` for state storage.
    :param default_rate: Default cooldown time if 'rate' flag is missing.
    :param default_key: Default scope key if 'key' flag is missing.
    """

    def __init__(self, redis: Redis, default_rate: int = 1, default_key: str = "common") -> None:
        self._cache = redis
        self._rate = default_rate
        self._rate_key = default_key

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        if not event.from_user:
            return await handler(event, data)

        rate_limit: dict = get_flag(data, "rate_limit")
        if not rate_limit:
            return await handler(event, data)

        rate = int(rate_limit.get("rate", self._rate))
        rate_key = rate_limit.get("key", self._rate_key)

        user_tg_id = event.from_user.id
        redis_key = f"throttle:{rate_key}:{user_tg_id}"

        if await self._cache.get(redis_key):
            flood_key = f"flood:{redis_key}"

            if await self._cache.incr(flood_key) <= 1:
                await self._cache.expire(flood_key, rate, nx=True)
                ttl = await self._cache.ttl(redis_key)
                text = THROTTLING_TEXT.format(ttl=ttl)
                logger.debug(f'Prevent flooding <user_id={user_tg_id} key="{rate_key}" rate={rate}s ttl={ttl}s>')
                return await answer_from_update(event, text, is_reply=True)
            return 0

        await self._cache.set(redis_key, 1, ex=rate, nx=True)

        return await handler(event, data)
