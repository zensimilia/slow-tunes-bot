import asyncio
from typing import Any, Callable

from aiogram import Bot
from aiogram.client.session.middlewares.base import BaseRequestMiddleware
from aiogram.exceptions import TelegramRetryAfter
from aiogram.methods import Response, TelegramMethod
from aiogram.methods.base import TelegramType


class RetryRequestMiddleware(BaseRequestMiddleware):
    async def __call__(
        self,
        make_request: Callable[[Bot, TelegramMethod[TelegramType]], Any],
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        try:
            return await make_request(bot, method)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            return await make_request(bot, method)
