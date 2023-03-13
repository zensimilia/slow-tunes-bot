import asyncio

from bot.config import AppConfig
from bot.utils.logger import get_logger
from bot.utils.redis import RedisClient
from bot.utils.singleton import singleton

log = get_logger()
config = AppConfig()
redis_client = RedisClient(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
)

QUEUE_KEY = "queue"


@singleton
class Queue:
    """A class that implements async queue for tasks."""

    def __init__(
        self,
        maxsize: int = 0,
    ) -> None:
        self._queue = asyncio.Queue(maxsize=maxsize)
        self._queue_size = 0
        self._redis = None
        self.count = 1

    async def start(self):
        """Starts loop worker for the queue."""

        log.info("Start tasks queue.")

        self._redis = await redis_client.get_redis()

        while True:  # TODO: implement stop()
            try:
                coro = await self._queue.get()
                log.debug("Run task #%d from the queue %s", self.count, coro)
                await asyncio.create_task(coro)
            except (asyncio.CancelledError, ValueError) as error:
                log.debug("Queue task #%d canceled %s", self.count, error)
            except Exception as error:  # pylint: disable=broad-except
                log.error("Exception in queue task: %s", error)
            else:
                log.debug("Queue task #%d done", self.count)
            finally:
                self._queue_size -= 1
                self.count += 1

    async def stop(self):
        """Stops loop worker for the queue."""
        await self._redis.close()
        await self._redis.wait_closed()

    def enqueue(self, func, *args, **kwargs) -> int:
        """Add a task into the queue."""

        self._queue_size += 1
        self._queue.put_nowait(func(*args, **kwargs))
        log.debug("Task #%d added to the queue %s", self.count, func)
        return self._queue_size

    async def get_user_queue(self, user_id: int) -> int:
        """It gets the user's queue from the database."""

        key = redis_client.generate_key(user_id, QUEUE_KEY)
        val = await self._redis.get(key)
        return int(val or 0)

    async def inc_user_queue(self, user_id: int) -> bool:
        """
        It increments the user's queue count by 1 and
        returns True if the operation was successful.
        """

        key = redis_client.generate_key(user_id, QUEUE_KEY)
        return bool(await self._redis.incr(key))

    async def dec_user_queue(self, user_id: int) -> bool:
        """
        It decrements the user's queue count by 1 and
        returns True if the operation was successful.
        """

        key = redis_client.generate_key(user_id, QUEUE_KEY)
        return bool(await self._redis.decr(key))

    @property
    def size(self):
        """Return the number of tasks in the queue."""

        return self._queue_size

    @property
    def is_empty(self):
        """Return True if the queue is empty, False otherwise."""

        return not bool(self.size)
