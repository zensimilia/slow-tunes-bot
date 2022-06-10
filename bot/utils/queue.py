import asyncio

from bot.utils.logger import get_logger
from bot.utils.singleton import singleton

log = get_logger()


@singleton
class Queue:
    """A class that implements async queue for tasks."""

    def __init__(
        self,
        maxsize: int = 0,
    ) -> None:
        self._queue = asyncio.Queue(maxsize=maxsize)
        self._queue_size = 0

    async def start(self):
        """Starts loop worker for the queue."""

        log.debug("Start worker for the main queue")

        while True:
            try:
                coro = await self._queue.get()
                log.debug("Run Task from the queue %s", coro)
                await asyncio.create_task(coro)
            except (asyncio.CancelledError, ValueError):
                pass
            finally:
                self._queue_size -= 1

    async def enqueue(self, func, *args, **kwargs) -> int:
        """Add a task into the queue."""

        await self._queue.put(func(*args, **kwargs))
        self._queue_size += 1
        log.debug("Task added to the queue %s", func)
        return self._queue_size

    @property
    def size(self):
        """Return the number of items in the queue."""

        return self._queue_size

    @property
    def is_empty(self):
        """Return `True` if the queue is empty, `False` otherwise."""

        return self._queue.empty()
