import asyncio
import os

from aiogram import types
from aiogram.utils.exceptions import FileIsTooBig, TelegramAPIError

from bot import db, keyboards
from bot.config import AppConfig
from bot.utils import audio
from bot.utils.logger import get_logger
from bot.utils.queue import Queue

config = AppConfig()
queue = Queue()
log = get_logger()


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


async def slowing_down_task(message: types.Message) -> bool:
    """Slowing down audio Task."""

    # Check if the audio has already slowed down
    # then returns it from telegram servers directly
    from_db = await db.get_match(message.audio.file_unique_id)
    if from_db:
        await message.answer_audio(
            from_db[2],
            caption="Slowed by @slowtunesbot",
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

        if slowed_down:
            await message.answer_chat_action(types.ChatActions.UPLOAD_AUDIO)

            file_name = audio.brand_file_name(message.audio.file_name)
            thumb_file_exists = os.path.exists(config.ALBUM_ART)
            tags = {
                'performer': message.audio.to_python().get("performer"),
                'title': message.audio.to_python().get("title"),
                'thumb': types.InputFile(config.ALBUM_ART)
                if thumb_file_exists
                else None,
            }
            uploaded = await message.answer_audio(
                types.InputFile(slowed_down, filename=file_name),
                caption="Slowed by @slowtunesbot",
                reply_markup=keyboards.share_button(
                    message.audio.file_unique_id,
                    True,
                ),
                **tags,
            )
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
        if slowed_down:
            os.remove(slowed_down)
