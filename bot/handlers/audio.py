import os

from aiogram import types
from aiogram.types.mixins import Downloadable
from aiogram.utils.exceptions import FileIsTooBig, TelegramAPIError

from bot import db, keyboards
from bot.config import AppConfig
from bot.utils.exceptions import QueueLimitReached
from bot.utils import audio
from bot.utils.brand import get_branded_file_name, get_caption
from bot.utils.logger import get_logger
from bot.utils.queue import Queue

config = AppConfig()
queue = Queue()
log = get_logger()


async def processing_audio(message: types.Message):
    """Slow down uploaded audio track and send it to user."""

    await message.answer_chat_action(types.ChatActions.TYPING)

    # Check file for size limit (20mb)
    if message.audio.file_size >= (20 * 1024 * 1024):
        raise FileIsTooBig(message.audio.file_size)

    # Checks if the audio has already slowed down then returns it
    # from telegram servers directly avoiding the queue
    if from_db := await db.get_match(message.audio.file_unique_id):
        (idc, file_unique_id, file_id, user_id, is_private, *_) = from_db

        if user_id == message.from_user.id:
            keyboard = keyboards.share_button(file_unique_id, is_private)
        else:
            is_liked = await db.is_liked(idc, message.from_user.id)
            keyboard = keyboards.random_buttons(idc, is_like=is_liked)

        return await message.answer_audio(
            file_id,
            caption=await get_caption(),
            reply_markup=keyboard,
        )

    queue_count = await db.get_queue_count(message.from_user.id)
    if queue_count >= config.TASK_LIMIT:
        raise QueueLimitReached(queue_count)

    await db.inc_queue_count(message.from_user.id)

    # Add slowing down audio task to the queue
    task = queue.enqueue(slowing_down_task, message)

    if task > 1:
        await message.reply(
            f"🕙 Added your request to the queue. Your position: {task}.",
            disable_notification=True,
        )


async def slowing_down_task(message: types.Message) -> bool:
    """Slowing down audio Task."""

    info_message = await message.reply(
        "💿 Start recording at 33 rpm for you...",
        disable_notification=True,
    )

    if not (downloaded := await download_file(message.audio)):
        await info_message.edit_text(
            "💾 Can't download your file. Please try again or come back later."
        )
        return False

    await message.answer_chat_action(types.ChatActions.RECORD_AUDIO)

    if not (slowed := await audio.slow_down(downloaded, config.SPEED_RATIO)):
        await info_message.edit_text(
            (
                "⚠ I have some issues with processing your audio. "
                "Please send me another file or try again later."
            )
        )
        return False

    await message.answer_chat_action(types.ChatActions.UPLOAD_AUDIO)

    try:
        file_name = await get_branded_file_name(
            message.audio.file_name or message.audio.file_unique_id
        )
        thumb_file_exists = os.path.exists(config.ALBUM_ART)
        tags = {
            "performer": message.audio.to_python().get("performer"),
            "title": message.audio.to_python().get("title"),
            "thumb": types.InputFile(config.ALBUM_ART)
            if thumb_file_exists
            else None,
        }
        uploaded = await message.answer_audio(
            types.InputFile(slowed, filename=file_name),
            caption=await get_caption(),
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

    except TelegramAPIError as error:
        log.error(error)
        await info_message.edit_text(
            (
                f"🤷‍♂️ I'm sorry {message.from_user.username}, "
                "I'm afraid I can't do that."
            )
        )
        return False

    finally:
        await db.dec_queue_count(message.from_user.id)
        os.remove(downloaded)
        os.remove(slowed)


async def download_file(obj: Downloadable, **kwargs) -> str | None:
    """Downloads a file and returns the path to
    the downloaded file or None if error occured."""

    options = {
        'destination_dir': config.DATA_DIR,
        **kwargs,
    }

    try:
        downloaded = await obj.download(**options)
        downloaded.close()
    except Exception as error:
        log.error(error)
        return None
    return downloaded.name
