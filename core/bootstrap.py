import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand
from redis.asyncio import Redis

from db.base import Database
from middlewares.auth import UserMiddleware
from middlewares.db import DbSessionMiddleware
from middlewares.retry import RetryRequestMiddleware
from middlewares.throttling import RateLimitMiddleware
from routes.admin import admin_router
from routes.audio import audio_router
from routes.common import common_router

from .config import config
from .queue import TaskQueue

DB_URL = f"sqlite+aiosqlite:///{config.DB_FILE.as_posix()}"

db = Database(DB_URL)
redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=0, decode_responses=True)
redis_storage = RedisStorage(redis)
queue = TaskQueue(maxsize=config.QUEUE_MAXSIZE)


async def set_bot_commands(bot: Bot, commands: list[BotCommand] | None = None) -> None:
    if commands is None:
        commands = [
            BotCommand(command="about", description="useful information"),
            BotCommand(command="help", description="if you stuck"),
            BotCommand(command="start", description="say hello"),
        ]
    await bot.set_my_commands(commands)


async def on_startup(bot: Bot, queue: TaskQueue) -> None:
    await db.create_tables()  # create tables if not exist
    queue_task = asyncio.create_task(queue.start())  # start task queue worker
    queue_task.set_name("queue")  # RUF006

    await bot.delete_webhook(drop_pending_updates=True)  # drop pending updates workaround
    await set_bot_commands(bot)  # register bot commands

    if not config.DEBUG:
        await bot.send_message(config.BOT_ADMIN_ID, "🟢 I'M ONLINE!")


async def on_shutdown(bot: Bot, dispatcher: Dispatcher) -> None:
    await dispatcher.storage.close()  # close storage
    await db.close_all()  # close all db sessions
    await set_bot_commands(bot, [])  # clear bot commands

    if not config.DEBUG:
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

    dispatcher.message.middleware(RateLimitMiddleware(redis))
    dispatcher.callback_query.middleware(RateLimitMiddleware(redis))
    dispatcher.update.outer_middleware(DbSessionMiddleware(db))
    dispatcher.update.outer_middleware(UserMiddleware(redis))

    return dispatcher


def setup_bot() -> Bot:
    session = AiohttpSession()
    session.middleware.register(RetryRequestMiddleware())
    properties = DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True)
    return Bot(token=config.BOT_TOKEN, default=properties, session=session)
