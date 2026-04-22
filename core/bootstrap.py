import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand
from redis.asyncio import Redis

from db.base import Database
from router.admin import admin_router
from router.audio import audio_router
from router.common import common_router

from .config import config
from .queue import TaskQueue

db = Database(f"sqlite+aiosqlite:///{config.DB_FILE.as_posix()}")
redis_fsm = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=0)
redis_storage = RedisStorage(redis_fsm)
queue = TaskQueue(maxsize=32)


async def set_bot_commands(bot: Bot, commands: list[BotCommand] | None = None) -> None:
    if commands is None:
        commands = [
            BotCommand(command="about", description="useful information"),
            BotCommand(command="help", description="if you stuck"),
            BotCommand(command="start", description="say hello"),
        ]
    await bot.set_my_commands(commands)


async def on_startup(bot: Bot, queue: TaskQueue):
    await db.create_tables()  # create tables if not exist
    asyncio.create_task(queue.start())  # start task queue worker

    await bot.delete_webhook(drop_pending_updates=True)  # drop pending updates woraround
    await set_bot_commands(bot)  # register bot commands
    await bot.send_message(config.BOT_ADMIN_ID, "🟢 I'M ONLINE!")


async def on_shutdown(bot: Bot, dispatcher: Dispatcher):
    await dispatcher.storage.close()  # close storage
    await set_bot_commands(bot, [])  # clear bot commands
    await db.close_all()  # close all db sessions
    await bot.send_message(config.BOT_ADMIN_ID, "🔴 I'M OFFLINE!")


def setup_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=redis_storage)
    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)

    dispatcher["db"] = db  # inject database
    dispatcher["queue"] = queue  # inject task queue

    dispatcher.include_router(admin_router)
    dispatcher.include_router(audio_router)
    dispatcher.include_router(common_router)

    return dispatcher


def setup_bot() -> Bot:
    properties = DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True)
    return Bot(token=config.BOT_TOKEN, default=properties)
