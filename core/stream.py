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
    """
    Asynchronous task manager based on Redis Streams and Consumer Groups.

    This class provides a reliable way to distribute tasks between multiple workers,
    supporting both coroutines and synchronous functions with automatic
    dependency injection (Bot instance).
    """

    def __init__(self, *, redis: Redis, bot: Bot, groupname: str = DEFAULT_GROUPNAME) -> None:
        """
        Initialize the task stream manager.

        Args:
            redis: An instance of `redis.asyncio.Redis`.
            bot: An instance of `aiogram.Bot` to be injected into task functions.
            groupname (optional): The name of the Redis consumer group.
                Defaults to `DEFAULT_GROUPNAME`.
        """
        self.__r = redis
        self.__bot = bot
        self.__groupname = groupname
        self.__streams = {}
        self.__streams_ready = asyncio.Event()
        self.__running = False
        self.__tasks = set()

    async def subscribe(self, name: str, func: TaskFunc, *, streamid: str = "$") -> None:
        """
        Subscribe a function to a specific stream.

        Creates a consumer group if it doesn't exist and registers the handler.

        Args:
            name: The name of the stream to subscribe to.
            func: The handler function (can be sync or async).
            streamid (optional): The ID to start reading from.
                Defaults to "$" (new messages).
        """
        with contextlib.suppress(ResponseError):
            await self.__r.xgroup_create(name, self.__groupname, id=streamid, mkstream=True)
        self.__streams.setdefault(name, []).append(func)
        self.__streams_ready.set()

    async def publish(self, name: str, payload: dict, *, maxlen: int = 1000) -> None:
        """
        Publish a task payload to a stream.

        Args:
            name: The name of the target stream.
            payload: Data dictionary representing the task.
            maxlen (optional): Maximum length of the stream (approximate).
                Defaults to 1000.
        """
        with contextlib.suppress(ResponseError):
            await self.__r.xadd(
                name=name,
                fields=payload,
                maxlen=maxlen,
                approximate=True,
            )

    async def __run(self, func: TaskFunc, payload: dict) -> None:
        """
        Take a task function and a payload, prepares the data based on the function's signature,
        and then executes the function either as a coroutine or in an executor.

        Args:
            func (TaskFunc): A function that will be executed asynchronously.
            payload: A dictionary containing data that will be passed as arguments to the `func` function.
        """
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
        """
        Process a task by running multiple functions concurrently, acknowledging and deleting
        the message from a stream, and logging any errors that occur.

        Args:
            stream: S string that represents the stream from which a task is being processed.
            msg_id: A unique identifier for the message being processed in the stream.
            payload: A dictionary containing data that needs to be processed by the functions
                associated with the specified stream.
        """
        try:
            funcs = self.__streams.get(stream, [])
            await asyncio.gather(*(self.__run(f, payload) for f in funcs))

            await self.__r.xack(stream, self.__groupname, msg_id)
            await self.__r.xdel(stream, msg_id)
        except Exception as err:  # noqa: BLE001
            logger.error(f"Failed to process task {msg_id} from {stream}: {err}")

    async def __react(self, events: list[tuple] | None) -> None:
        """
        Process a list of events by decoding payloads and creating tasks to process each event asynchronously.

        Args:
            events (optional): A list of tuples where each tuple contains a stream and a message.
                Defaults to None.
        """
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
        """
        Start the infinite loop to listen for and process incoming tasks.

        Args:
            consumer_name: Unique identifier for this consumer instance.

        Examples:
            ```python
            stream = TaskStream(redis=redis, bot=bot)
            await stream.subscribe("orders", process_order)
            await stream.listen("worker-1")
            ```
        """
        if not self.__streams:
            logger.warning("No streams to listen. Call subscribe() first")
            await self.__streams_ready.wait()

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
        """
        Gracefully stop the listener and wait for pending tasks.

        Args:
            purge (optional): If True, destroys consumer groups for all subscribed streams.
                Defaults to False.
        """
        self.__running = False
        if self.__tasks:
            await asyncio.wait(self.__tasks, timeout=5)
        if purge:
            [await self.unsubscribe(s) for s in self.__streams]

    async def unsubscribe(self, name: str) -> None:
        """
        Remove the consumer group from a specific stream.

        Args:
            name: The name of the stream to unsubscribe from.
        """
        await self.__r.xgroup_destroy(name, self.__groupname)
        logger.info(f"Unsubscribe '{name}' from '{self.__groupname}'")
