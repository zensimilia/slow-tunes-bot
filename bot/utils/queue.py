from __future__ import annotations

import asyncio

from bot.config import AppConfig
from bot.utils.logger import get_logger
from bot.utils.redis import RedisClient

log = get_logger()
config = AppConfig()
redis_client = RedisClient(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
)

QUEUE_KEY = "queue"


class Queue:
    """A class that implements async queue for tasks."""

    def __init__(self, maxsize: int = 0) -> None:
        self.__queue = asyncio.Queue(maxsize=maxsize)
        self.__running = False
        self.__storage = None
        self.__size = 0
        self.count = 1

    @classmethod
    async def create(cls, maxsize: int = 0) -> Queue:
        """It creates a Queue object."""

        self = Queue(maxsize=maxsize)
        self.__storage = await redis_client.get_redis()
        return self

    async def start(self):
        """Starts loop worker for the queue."""

        log.info("Start tasks queue.")

        self.__running = True

        while self.__running:
            try:
                coro = await self.__queue.get()
                log.debug("Run task #%d from the queue %s", self.count, coro)
                await asyncio.create_task(coro)
            except (asyncio.CancelledError, ValueError) as error:
                log.debug("Queue task #%d canceled %s", self.count, error)
            except Exception as error:  # pylint: disable=broad-except
                log.error("Exception in queue task: %s", error)
            else:
                log.debug("Queue task #%d done", self.count)
            finally:
                self.__size -= 1
                self.count += 1

    async def stop(self):
        """Stops loop worker for the queue."""

        self.__running = False

        await self.__storage.close()
        await self.__storage.wait_closed()

    def enqueue(self, func, *args, **kwargs) -> int:
        """Add a task into the queue."""

        self.__size += 1
        self.__queue.put_nowait(func(*args, **kwargs))
        log.debug("Task #%d added to the queue %s", self.count, func)
        return self.__size

    async def get_user_queue(self, user_id: int) -> int:
        """It gets the user's queue from the database."""

        key = redis_client.generate_key(user_id, QUEUE_KEY)
        val = await self.__storage.get(key)
        return int(val or 0)

    async def inc_user_queue(self, user_id: int) -> bool:
        """
        It increments the user's queue count by 1 and
        returns True if the operation was successful.
        """

        key = redis_client.generate_key(user_id, QUEUE_KEY)
        return bool(await self.__storage.incr(key))

    async def dec_user_queue(self, user_id: int) -> bool:
        """
        It decrements the user's queue count by 1 and
        returns True if the operation was successful.
        """

        key = redis_client.generate_key(user_id, QUEUE_KEY)
        return bool(await self.__storage.decr(key))

    @property
    def size(self):
        """Return the number of tasks in the queue."""

        return self.__size

    @property
    def is_empty(self):
        """Return True if the queue is empty, False otherwise."""

        return not bool(self.__size)
