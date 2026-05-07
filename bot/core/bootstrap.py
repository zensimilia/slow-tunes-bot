import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand
from redis.asyncio import Redis

from bot.config import config
from bot.middlewares.auth import UserMiddleware
from bot.middlewares.db import DbSessionMiddleware
from bot.middlewares.retry import RetryRequestMiddleware
from bot.middlewares.throttling import RateLimitMiddleware
from bot.routes import admin_router, audio_router, common_router
from bot.services.queue import TaskQueue
from bot.services.stream import TaskStream
from db.engine import Database

DB_URL = f"sqlite+aiosqlite:///{config.DB_FILE.as_posix()}"
STREAM_CONSUMER_NAME = "main"

db = Database(DB_URL)
redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=0, decode_responses=True)
background_tasks = set()


async def set_bot_commands(bot: Bot, commands: list[BotCommand] | None = None) -> None:
    if commands is None:
        commands = [
            BotCommand(command="about", description="useful information"),
            BotCommand(command="help", description="if you stuck"),
            BotCommand(command="start", description="say hello"),
        ]
    await bot.set_my_commands(commands)


async def on_startup(bot: Bot, dispatcher: Dispatcher) -> None:
    await bot.delete_webhook(drop_pending_updates=True)  # drop pending updates workaround
    await set_bot_commands(bot)  # register bot commands

    await db.create_tables()  # create tables if not exist
    dispatcher["db"] = db  # inject database

    queue = TaskQueue(maxsize=config.QUEUE_MAXSIZE)
    queue_task = asyncio.create_task(queue.start())  # start task queue worker
    background_tasks.add(queue_task)
    dispatcher["queue"] = queue  # inject task queue

    stream = TaskStream(redis=redis, bot=bot)
    stream_task = asyncio.create_task(stream.listen(STREAM_CONSUMER_NAME))  # listen streams
    background_tasks.add(stream_task)
    dispatcher["stream"] = stream  # inject streams

    setup_routes(dispatcher)
    setup_middlewares(dispatcher)

    await bot.send_message(config.BOT_ADMIN_ID, "🟢 I'M ONLINE!")


async def on_shutdown(bot: Bot, dispatcher: Dispatcher) -> None:
    await dispatcher.storage.close()  # close storage
    await db.close_all()  # close all db sessions
    await set_bot_commands(bot, [])  # clear bot commands

    dispatcher["queue"].stop()
    await dispatcher["stream"].stop()

    await bot.send_message(config.BOT_ADMIN_ID, "🔴 I'M OFFLINE!")

    await bot.session.close()


def setup_routes(dispatcher: Dispatcher) -> None:
    dispatcher.include_router(admin_router)
    dispatcher.include_router(audio_router)
    dispatcher.include_router(common_router)


def setup_middlewares(dispatcher: Dispatcher) -> None:
    dispatcher.message.middleware(RateLimitMiddleware(redis))
    dispatcher.callback_query.middleware(RateLimitMiddleware(redis))
    dispatcher.update.outer_middleware(DbSessionMiddleware(db))
    dispatcher.update.outer_middleware(UserMiddleware(redis))


def setup_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=RedisStorage(redis))
    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)
    return dispatcher


def setup_bot() -> Bot:
    session = AiohttpSession(proxy=config.TELEGRAM_PROXY_URL)
    session.middleware.register(RetryRequestMiddleware())
    properties = DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True)
    return Bot(token=config.BOT_TOKEN, default=properties, session=session)
