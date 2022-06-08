import asyncio
import os
from concurrent.futures import ProcessPoolExecutor

from aiogram import Dispatcher, types
from aiogram.utils.exceptions import FileIsTooBig, Throttled, TelegramAPIError
from pydub.exceptions import PydubException

from bot import db
from bot import errors as eh
from bot.config import AppConfig
from bot.utils import audio
from bot.utils.logger import get_logger
from bot.utils.queue import Queue

log = get_logger()
config = AppConfig()
queue = Queue()


def register_handlers(dp: Dispatcher):
    """Register all the Bot's handlers."""

    log.info("Register Bot handlers...")

    dp.register_errors_handler(
        eh.file_is_too_big,
        exception=FileIsTooBig,
    )
    dp.register_errors_handler(
        eh.global_error_handler, exception=Exception
    )  # Should be last among errors handlers

    dp.register_message_handler(
        command_start,
        commands=["start"],
    )
    dp.register_message_handler(
        command_random,
        commands=["random"],
    )
    dp.register_message_handler(
        processing_audio,
        content_types=[types.ContentType.AUDIO],
    )
    dp.register_message_handler(answer_message)


async def processing_audio(message: types.Message):
    """Slow down uploaded audio track and send it to user."""

    dp = Dispatcher.get_current()

    # Execute throttling manager
    try:
        await dp.throttle('processing_audio', rate=config.THROTTLE_RATE)
    except Throttled:
        log.debug(
            "Throttled <user_id=%s file_id=%s>",
            message.from_user.id,
            message.audio.file_id,
        )
        await message.answer('Too many requests! Calm bro!')
        return

    # Check if audio is already slowed then return it from telegram servers
    from_db = await db.get_match(message.audio.file_unique_id)
    if from_db:
        await message.answer(
            "Delivery from past...",
            disable_notification=True,
        )
        await message.answer_audio(
            from_db[2],
            # caption="@slowtunesbot",
        )
        return

    # Check file for size limit (20mb)
    if message.audio.file_size >= (20 * 1024 * 1024):
        raise FileIsTooBig("File is too big")

    task = await queue.enqueue(slowing_down_task, message)

    text_message = "Start recording at 33 rpm for you..."
    if task > 1:
        text_message = (
            f"Added your request to the queue! Your position: {task}."
        )

    await message.answer(
        text_message,
        disable_notification=True,
    )


async def answer_message(message: types.Message):
    """Handler for debug incoming messages."""

    await message.answer(
        "Throw an audio. I'll catch! \nSend /help for additional information."
    )


async def command_random(message: types.Message):
    """Handler for `/random` command. Returns random tune from database."""

    random = await db.get_random_match()
    if random:
        await message.answer("Some slow tune for you...")
        await message.answer_audio(random[0], caption="@slowtunesbot")
        return

    log.info("No tunes in database for /random command")
    await message.answer("Sorry, but I don't have tunes yet.")


async def command_start(message: types.Message):
    """Handler for `/start` command."""

    log.info(
        "User join: %s <%s>", message.from_user.id, message.from_user.username
    )
    await message.answer("Send me the audio track " "and i will...")


async def slowing_down_task(message: types.Message) -> bool:
    """Slowing down audio Task."""

    downloaded = None
    await message.answer_chat_action(types.ChatActions.RECORD_AUDIO)

    try:
        downloaded = await message.audio.download(
            destination_dir=config.DATA_DIR
        )

        # Gets current loop and run slowing down func in other pool executor
        # to not block the Bot
        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor() as pool:
            slowed_down = await loop.run_in_executor(
                pool, audio.slow_down, downloaded.name, config.SPEED_RATIO
            )

        tags = {
            'performer': message.audio.to_python().get('performer'),
            'title': " ".join([message.audio.title, "@slowtunesbot"]),
            # 'thumb': types.InputFile(os.path.join(config.DATA_DIR, 'thumb.jpg')),
        }

        if slowed_down:
            await message.answer_chat_action(types.ChatActions.UPLOAD_AUDIO)

            file_name = audio.brand_file_name(message.audio.file_name)
            uploaded = await message.answer_audio(
                types.InputFile(slowed_down, filename=file_name),
                # caption="@slowtunesbot",
                **tags,
            )
            os.remove(slowed_down)
            await db.insert_match(
                message.audio.file_unique_id,
                uploaded.audio.file_id,
            )
            return True
    except (PydubException, TelegramAPIError) as error:
        log.error(error)
    finally:
        if downloaded:
            downloaded.close()
            os.remove(downloaded.name)

    await message.answer_chat_action(types.ChatActions.TYPING)

    await message.answer(
        f"I'm Sorry {message.from_user.username}, I'm Afraid I Can't Do That."
    )
    return False
