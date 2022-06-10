import asyncio
import os

from aiogram import Dispatcher, types
from aiogram.utils.exceptions import FileIsTooBig, TelegramAPIError

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
        eh.database_error,
        exception=db.Error,
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

    # Check file for size limit (20mb)
    if message.audio.file_size >= (20 * 1024 * 1024):
        raise FileIsTooBig("File is too big")

    # Add slowing down audio task to the queue
    await queue.enqueue(slowing_down_task, message)

    if queue.size > 1:
        await message.reply(
            f"🕙 Added your request to the queue. Your position: {queue.size}.",
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

    # Check if the audio has already slowed down
    # then returns it from telegram servers directly
    from_db = await db.get_match(message.audio.file_unique_id)
    if from_db:
        await message.answer_audio(
            from_db[2],
            # caption="@slowtunesbot",
        )
        return True

    downloaded = None

    await message.reply(
        "💿 Start recording at 33 rpm for you...",
        disable_notification=True,
    )
    await message.answer_chat_action(types.ChatActions.RECORD_AUDIO)

    try:
        downloaded = await message.audio.download(
            destination_dir=config.DATA_DIR
        )

        # Run func in separate thread for unblock stack
        slowed_down = await asyncio.to_thread(
            audio.slow_down, downloaded.name, config.SPEED_RATIO
        )

        tags = {
            'performer': message.audio.to_python().get("performer"),
            'title': " ".join(
                [message.audio.to_python().get("title", ""), "@slowtunesbot"]
            ),
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
                message.from_user.id,
            )
            return True
        await message.reply(
            "⚠ I have some issues with decoding your audio file. Please try another..."
        )
        return False
    except TelegramAPIError as error:
        log.error(error)
        await message.reply(
            f"🤷‍♂️ I'm sorry {message.from_user.username}, I'm afraid I can't do that."
        )
        return False
    finally:
        if downloaded:
            downloaded.close()
            os.remove(downloaded.name)
