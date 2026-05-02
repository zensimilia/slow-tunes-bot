import asyncio
import contextlib
import inspect
from collections.abc import Awaitable, Callable
from functools import partial
from typing import TYPE_CHECKING, Any

from redis.exceptions import ResponseError

from core.exceptions import NoStreamsError

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
        self.__tasks = set()

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
        sig = inspect.signature(func)
        has_kwargs = any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values())

        data = payload if has_kwargs else {k: v for k, v in payload.items() if k in sig.parameters}

        if "bot" in sig.parameters or has_kwargs:
            data["bot"] = self.__bot

        if inspect.iscoroutinefunction(func):
            await func(**data)
        else:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, partial(func, **data))

    async def __process_task(self, stream: str, msg_id: str, payload: dict) -> None:
        try:
            funcs = self.__streams.get(stream, [])
            await asyncio.gather(*(self.__run(f, payload) for f in funcs))

            await self.__r.xack(stream, self.__groupname, msg_id)
            await self.__r.xdel(stream, msg_id)
        except Exception as err:  # noqa: BLE001
            logger.error(f"Failed to process task {msg_id} from {stream}: {err}")

    async def __react(self, events: list[tuple] | None) -> None:
        if not events:
            return

        for stream, message in events:
            for msg_id, payload in message:
                decoded_payload = {
                    k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
                    for k, v in payload.items()
                }
                logger.debug(f"Processing task #{msg_id} from {stream}")
                task = asyncio.create_task(self.__process_task(stream, msg_id, decoded_payload))
                self.__tasks.add(task)
                task.add_done_callback(self.__tasks.discard)

    async def listen(self, consumer_name: str) -> None:
        if not self.__streams:
            raise NoStreamsError

        logger.info(f"Stream listener '{self.__groupname}' started")

        self.__running = True
        while self.__running:
            try:
                events = await self.__r.xreadgroup(
                    groupname=self.__groupname,
                    consumername=consumer_name,
                    streams=dict.fromkeys(self.__streams, "0"),
                    count=10,
                    block=1000,
                )
                await self.__react(events)
            except Exception as err:  # noqa: BLE001
                logger.error(err)
                await asyncio.sleep(3)

        logger.info(f"Stream listener '{self.__groupname}' stopped")

    async def stop(self, *, purge: bool = False) -> None:
        self.__running = False
        if self.__tasks:
            await asyncio.wait(self.__tasks, timeout=5)
        if purge:
            [await self.unsubscribe(s) for s in self.__streams]

    async def unsubscribe(self, name: str) -> None:
        await self.__r.xgroup_destroy(name, self.__groupname)
        logger.info(f"Unsubscribe '{name}' from '{self.__groupname}'")
