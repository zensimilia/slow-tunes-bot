from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from bot.config import AppConfig
from bot.db import init_sqlite
from bot.handlers import register_handlers
from bot.utils.logger import get_logger
from bot.utils.queue import BotQueue

log = get_logger(__name__)
config = AppConfig()
storage = MemoryStorage()
queue = BotQueue()


async def on_startup(dp: Dispatcher):
    """Execute function before Bot start polling."""

    log.info("Execute startup Bot functions...")
    init_sqlite()
    register_handlers(dp)

    commands = [
        types.BotCommand('random', 'get some slowed tune'),
        types.BotCommand('donate', 'buy me a beer'),
        types.BotCommand('help', 'if you stuck'),
        types.BotCommand('about', 'bot info'),
    ]
    await dp.bot.set_my_commands(commands)

    test1 = await queue.enqueue(test, "lol")
    test2 = await queue.enqueue(test, "rolf")
    print(test1)
    print(test2)


async def on_shutdown(_dp: Dispatcher):
    """Execute function before Bot shut down polling."""

    log.info("Execute shutdown Bot functions...")


async def test(text):
    for x in range(30000000):
        y = x ^ x
    print(f"test: {text}")
    return f"return: {text}"


def main():
    """Main app runner."""

    bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
    dp = Dispatcher(bot, storage=storage)

    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
    )
    queue.start()


if __name__ == '__main__':
    main()
