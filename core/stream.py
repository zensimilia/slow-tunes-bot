import asyncio
import contextlib
import inspect
from collections.abc import Awaitable, Callable
from functools import partial
from typing import TYPE_CHECKING, Any

from redis.exceptions import ResponseError

from .logger import logger

if TYPE_CHECKING:
    from aiogram import Bot
    from redis.asyncio import Redis

TaskFunc = Callable[..., Any] | Callable[..., Awaitable[Any]]

DEFAULT_GROUPNAME = "bot"


class TaskStream:
    def __init__(self, *, redis: Redis, bot: Bot, groupname: str = DEFAULT_GROUPNAME) -> None:
        self.__r = redis
        self.__bot = bot
        self.__groupname = groupname
        self.__streams = {}
        self.__running = False

    async def subscribe(self, name: str, func: TaskFunc, *, streamid: str = "$") -> None:
        with contextlib.suppress(ResponseError):
            await self.__r.xgroup_create(name, self.__groupname, id=streamid, mkstream=True)
        self.__streams.setdefault(name, []).append(func)

    async def publish(self, name: str, payload: dict, *, maxlen: int = 1000) -> None:
        with contextlib.suppress(ResponseError):
            await self.__r.xadd(
                name=name,
                fields=payload,
                maxlen=maxlen,
                approximate=True,
            )

    async def __run(self, func: TaskFunc, payload: dict) -> None:
        if inspect.iscoroutinefunction(func):
            await func(**payload, bot=self.__bot)
        else:
            pfunc = partial(func, **payload, bot=self.__bot)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, pfunc)

    async def __react(self, events: list[tuple]) -> None:
        for stream, message in events:
            for msg_id, payload in message:
                for func in self.__streams.get(stream, []):
                    try:
                        logger.debug(f"Processing task #{msg_id}")
                        await self.__run(func, payload)
                        await self.__r.xack(stream, self.__groupname, msg_id)
                        await self.__r.xdel(stream, msg_id)
                    except ResponseError as err:
                        logger.warning(err)

    async def listen(self, consumer_name: str) -> None:
        if not self.__streams:
            raise ValueError  # TODO

        logger.info(f"Stream listener '{self.__groupname}' started")

        self.__running = True
        while self.__running:
            try:
                events = await self.__r.xreadgroup(
                    groupname=self.__groupname,
                    consumername=consumer_name,
                    streams=dict.fromkeys(self.__streams, ">"),
                    count=1,
                    block=100,
                )
                await self.__react(events)
            except Exception as err:
                logger.error(err)
                await asyncio.sleep(3)

        logger.info(f"Stream listener '{self.__groupname}' stopped")

    async def stop(self, *, purge: bool = False) -> None:
        self.__running = False
        if purge:
            [await self.unsubscribe(s) for s in self.__streams]

    async def unsubscribe(self, name: str) -> None:
        await self.__r.xgroup_destroy(name, self.__groupname)
