import asyncio

from bot.utils.logger import get_logger
from bot.utils.singleton import singleton

log = get_logger()


@singleton
class Queue:
    """A class that implements async queue."""

    def __init__(
        self,
        maxsize: int = 0,
    ) -> None:
        self._queue = asyncio.Queue(maxsize=maxsize)

    async def start(self):
        """Starts loop worker for the queue."""

        log.debug("Start the worker for main queue")
        while True:
            try:
                task = await self._queue.get()
                log.debug("Run Task from the queue %s", task)
                await asyncio.create_task(task)
            except (asyncio.CancelledError, ValueError) as error:
                log.warning(error)

    async def enqueue(self, func, *args, **kwargs) -> int:
        """Add a task into the queue."""

        await self._queue.put(func(*args, **kwargs))
        log.debug("New Task added to the queue")
        return self.size

    @property
    def size(self):
        """Return the number of items in the queue."""

        return self._queue.qsize()

    @property
    def is_empty(self):
        """Return `True` if the queue is empty, `False` otherwise."""

        return self._queue.empty()
