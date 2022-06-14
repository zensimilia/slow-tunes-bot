import asyncio

from aiogram import Dispatcher, types
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled

from bot.utils.logger import get_logger

log = get_logger()


class ThrottlingMiddleware(BaseMiddleware):
    """Throttling middleware."""

    def __init__(self, handlers: list[str] | None = None, *, rate: int = 10):
        self.handlers = handlers
        self.rate = rate
        super().__init__()

    async def on_process_message(self, message: types.Message, _data: dict):
        """This handler is called when dispatcher receives a message."""

        # Get current handler and return if it was not configured
        handler = current_handler.get()
        if not handler:
            return
        key = handler.__name__

        # Get dispatcher from context
        dispatcher = Dispatcher.get_current()

        # Return if current handler not in list of active handlers
        if self.handlers and key not in self.handlers:
            return

        # Use Dispatcher.throttle method
        try:
            await dispatcher.throttle(key, rate=self.rate)
        except Throttled as error:
            log.debug(
                "Prevent flooding <user_id=%s handler=%s>",
                message.from_user.id,
                key,
            )
            # Execute action
            await self.message_throttled(message, error)
            # Cancel current handler
            raise CancelHandler() from error

    @staticmethod
    async def message_throttled(message: types.Message, throttled: Throttled):
        """Notify user on first exceed."""

        # Calculate how many time is left till the block ends
        delta = throttled.rate - throttled.delta  # type:ignore

        # Prevent flooding
        if throttled.exceeded_count <= 2:
            await message.reply(
                f"✋ Too many requests! Calm bro! Wait for {delta:.0f} sec."
            )

        # Sleep
        await asyncio.sleep(delta)
