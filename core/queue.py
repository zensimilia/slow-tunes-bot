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
        logger.info("Queue worker started")

        while self.__running:
            try:
                func, args, kwargs = await self.__queue.get()
                logger.debug(f"Processing task #{self.count}")
                await func(*args, **kwargs)
                self.count += 1
            except asyncio.QueueShutDown:
                self.__running = False
                message = f"Queue worker stopped. Tasks in the queue: {self.size}. Tasks completed: {self.count}"
                logger.warning(message)
                break
            except Exception as err:
                logger.error(f"Task #{self.count} failed: {err}")
            finally:
                self.__queue.task_done()

    def enqueue(self, func: Callable[..., Any], *args, **kwargs) -> int:
        try:
            self.__queue.put_nowait((func, args, kwargs))
            return self.__queue.qsize()
        except (asyncio.QueueFull, asyncio.QueueShutDown) as err:
            logger.warning(f"Failed to enqueue task #{self.count}: queue is full")
            raise TaskQueueError from err

    @property
    def size(self):
        return self.__queue.qsize()

    def stop(self):
        self.__queue.shutdown(True)
