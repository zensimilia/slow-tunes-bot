import asyncio
from typing import Any, Callable

from loguru import logger


class TaskQueueError(Exception): ...


class TaskQueue:
    def __init__(self, maxsize: int = 0) -> None:
        self.__queue = asyncio.Queue(maxsize=maxsize)
        self.__running = False
        self.count = 0

    async def start(self) -> None:
        if self.__running:
            logger.warning("Queue worker is already running")
            return

        self.__running = True

        maxsize = self.__queue.maxsize if self.__queue.maxsize > 0 else "infinite"
        logger.info(f"Queue worker started with maxsize={maxsize}")

        while self.__running:
            try:  # get task from the queue
                func, args, kwargs = await self.__queue.get()
            except asyncio.QueueShutDown:
                self.__running = False
                break

            try:  # execute the task
                self.count += 1
                logger.debug(f"Processing task #{self.count}")
                await func(*args, **kwargs)
            except Exception as err:
                logger.error(f"Task #{self.count} failed: {err}")
            finally:
                self.__queue.task_done()

    def enqueue(self, func: Callable[..., Any], *args, **kwargs) -> int:
        try:  # add task to the queue
            self.__queue.put_nowait((func, args, kwargs))
        except (asyncio.QueueFull, asyncio.QueueShutDown) as err:
            reason = "full" if isinstance(err, asyncio.QueueFull) else "shut down"
            logger.warning(f"Failed to enqueue task #{self.count}: queue is {reason}")
            raise TaskQueueError from err
        return self.__queue.qsize()

    @property
    def size(self):
        return self.__queue.qsize()

    def stop(self):
        self.__queue.shutdown(True)
        message = f"Queue worker stopped. Tasks in the queue: {self.size}. Tasks completed: {self.count}"
        logger.warning(message)
