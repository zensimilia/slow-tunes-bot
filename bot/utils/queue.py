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
        self.count = 1

    async def start(self):
        """Starts loop worker for the queue."""

        log.info("Start tasks queue.")

        while True:
            try:
                coro = await self._queue.get()
                log.debug("Run task #%d from the queue %s", self.count, coro)
                await asyncio.create_task(coro)
            except (asyncio.CancelledError, ValueError) as error:
                log.debug("Queue task #%d canceled %s", self.count, error)
            except Exception as error:
                log.error("Exception in queue task: %s", error)
            else:
                log.debug("Queue task #%d done", self.count)
            finally:
                self._queue_size -= 1
                self.count += 1

    def enqueue(self, func, *args, **kwargs) -> int:
        """Add a task into the queue."""

        self._queue_size += 1
        self._queue.put_nowait(func(*args, **kwargs))
        log.debug("Task #%d added to the queue %s", self.count, func)
        return self._queue_size

    @property
    def size(self):
        """Return the number of tasks in the queue."""

        return self._queue_size

    @property
    def is_empty(self):
        """Return True if the queue is empty, False otherwise."""

        return not bool(self.size)
