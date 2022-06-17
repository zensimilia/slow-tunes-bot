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

    async def check_for_throttling(
        self, obj: types.Message | types.CallbackQuery
    ):
        """Common method for checking request for throttling."""

        # Get dispatcher from context
        dispatcher = Dispatcher.get_current()

        # Get current handler and return if it was not configured
        handler = current_handler.get(None)
        if not handler:
            return

        key = handler.__name__

        # Return if current handler not in list of active handlers
        if self.handlers and key not in self.handlers:
            return

        # Use Dispatcher.throttle method
        try:
            await dispatcher.throttle(key, rate=self.rate)
        except Throttled as error:
            log.debug(
                "Prevent flooding <user_id=%s handler=%s>",
                obj.from_user.id,
                key,
            )

            # Execute action
            if isinstance(obj, types.Message):
                await self.message_throttled(obj, error)
            else:
                await self.query_throttled(obj, error)

            # Cancel current handler
            raise CancelHandler() from error

    async def on_process_callback_query(
        self, query: types.CallbackQuery, _data: dict
    ):
        """This handler is called when dispatcher receives a callback query."""

        return await self.check_for_throttling(query)

    async def on_process_message(self, message: types.Message, _data: dict):
        """This handler is called when dispatcher receives a message."""

        return await self.check_for_throttling(message)

    @staticmethod
    async def message_throttled(message: types.Message, throttled: Throttled):
        """Notify user by messgae on first exceed."""

        # Calculate how many time is left till the block ends
        delta = throttled.rate - throttled.delta  # type:ignore

        # Prevent flooding
        if throttled.exceeded_count <= 2:
            await message.reply(
                f"✋ Too many requests! Calm bro! Wait for {delta:.0f} sec."
            )

        # Sleep
        await asyncio.sleep(delta)

    @staticmethod
    async def query_throttled(query: types.CallbackQuery, throttled: Throttled):
        """Notify user by query answer on first exceed."""

        # Calculate how many time is left till the block ends
        delta = throttled.rate - throttled.delta  # type:ignore

        # Prevent flooding
        if throttled.exceeded_count <= 2:
            await query.answer(
                f"✋ Too many requests! Calm bro! Wait for {delta:.0f} sec.",
                show_alert=True,
            )

        # Sleep
        await asyncio.sleep(delta)
