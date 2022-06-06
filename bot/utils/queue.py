import asyncio
from typing import Union

from bot.utils.logger import get_logger

log = get_logger()


class BotQueue:
    """A class that implements queue for telegram bot."""

    def __init__(
        self,
        maxsize: int = 0,
        name: Union[str, None] = None,
    ) -> None:
        self._queue = asyncio.Queue(maxsize=maxsize)
        self.name = name

    async def start(self):
        while True:
            try:
                task = await self._queue.get()
                self._queue.task_done()
                yield task
            except (asyncio.CancelledError, ValueError) as error:
                log.warning(error)

    async def enqueue(self, func, *args, **kwargs) -> int:
        task = asyncio.create_task(func(*args, **kwargs))
        await self._queue.put(task)

        return self._queue.qsize()
