import asyncio
import inspect
from functools import partial
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    TaskFunc = Callable[..., Any] | Callable[..., Awaitable[Any]]


class TaskQueueError(Exception):
    """Base Task Queue Exception."""


class TaskQueue:
    """
    An asynchronous task queue with support for both synchronous and asynchronous functions.

    This class manages a worker that processes tasks sequentially. Synchronous tasks
    are automatically offloaded to a thread pool executor to prevent blocking
    the event loop, while asynchronous tasks are awaited directly.

    Attributes:
        count: Total number of tasks processed since the worker started.
    """

    def __init__(self, maxsize: int = 0) -> None:
        """
        Initialize the TaskQueue.

        Args:
            maxsize (optional): Maximum number of items allowed in the queue.
                Defaults to 0.
        """
        self.__queue = asyncio.Queue(maxsize=maxsize)
        self.__running = False
        self.__busy = False
        self.count = 0

    async def start(self) -> None:
        """
        Starts the background worker to process tasks from the queue.

        The worker runs in an infinite loop until the queue is shut down.
        It automatically detects 'async def' functions and awaits them,
        while standard 'def' functions are run in the default loop executor.
        """
        if self.__running:
            logger.warning("Queue worker is already running")
            return

        self.__running = True

        maxsize = self.__queue.maxsize if self.__queue.maxsize > 0 else "infinite"
        logger.info(f"Queue worker started with maxsize={maxsize}")

        while self.__running:
            try:  # get task from the queue
                func, args, kwargs = await self.__queue.get()
                self.__busy = True
            except asyncio.QueueShutDown:
                self.__running = False
                break

            try:  # execute the task
                self.count += 1
                logger.debug(f"Processing task #{self.count}")

                if inspect.iscoroutinefunction(func):
                    await func(*args, **kwargs)
                else:
                    pfunc = partial(func, *args, **kwargs)
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, pfunc)
            except Exception as err:  # noqa: BLE001
                logger.error(f"Task #{self.count} failed: {err}")
            finally:
                self.__busy = False
                self.__queue.task_done()

    def enqueue(self, func: TaskFunc, *args: Any, **kwargs: Any) -> None:
        """
        Adds a new task to the queue without blocking.

        Args:
            func (TaskFunc): The function to be executed. Can be sync or async.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Raises:
            TaskQueueError: If the queue is full or has been shut down.
        """
        try:  # add task to the queue
            self.__queue.put_nowait((func, args, kwargs))
        except (asyncio.QueueFull, asyncio.QueueShutDown) as err:
            reason = "full" if isinstance(err, asyncio.QueueFull) else "shut down"
            logger.warning(f"Failed to enqueue task #{self.count}: queue is {reason}")
            raise TaskQueueError from err

    def stop(self) -> None:
        """
        Gracefully shuts down the queue and stops the worker.

        This method triggers a QueueShutDown exception in the worker loop.
        """
        self.__queue.shutdown(immediate=True)
        message = f"Queue worker stopped. Tasks in the queue: {self.size}. Tasks completed: {self.count}"
        logger.warning(message)

    @property
    def size(self) -> int:
        """Returns the current number of tasks waiting in the queue."""
        return self.__queue.qsize()

    @property
    def is_busy(self) -> bool:
        """Returns True if worker is busy or Queue is not empty."""
        return self.__busy or not self.__queue.empty()

    @property
    def total_pending(self) -> int:
        """Total Tasks in the Queue + one in the worker now."""
        return self.__queue.qsize() + (1 if self.__busy else 0)
