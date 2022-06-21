import os

from aiogram import types
from aiogram.utils.exceptions import FileIsTooBig, TelegramAPIError

from bot import db, keyboards
from bot.config import AppConfig
from bot.utils import audio
from bot.utils.brand import get_caption, get_branded_file_name
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
    if from_db := await db.get_match(message.audio.file_unique_id):
        (idc, _, file_id, *_) = from_db
        is_liked = await db.is_liked(idc, message.from_user.id)
        await message.answer_audio(
            file_id,
            caption=await get_caption(),
            reply_markup=keyboards.random_buttons(
                idc,
                is_like=is_liked,
            ),
        )
        return True

    downloaded = None

    info_message = await message.reply(
        "💿 Start recording at 33 rpm for you...",
        disable_notification=True,
    )
    await message.answer_chat_action(types.ChatActions.RECORD_AUDIO)

    try:
        downloaded = await message.audio.download(
            destination_dir=config.DATA_DIR
        )

        slowed_down = await audio.slow_down(downloaded.name, config.SPEED_RATIO)

        if slowed_down:
            await message.answer_chat_action(types.ChatActions.UPLOAD_AUDIO)

            file_name = await get_branded_file_name(message.audio.file_name)
            thumb_file_exists = os.path.exists(config.ALBUM_ART)
            tags = {
                "performer": message.audio.to_python().get("performer"),
                "title": message.audio.to_python().get("title"),
                "thumb": types.InputFile(config.ALBUM_ART)
                if thumb_file_exists
                else None,
            }
            uploaded = await message.answer_audio(
                types.InputFile(slowed_down, filename=file_name),
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
        await message.reply(
            (
                "⚠ I have some issues with processing your audio. "
                "Please send another file or try later."
            )
        )
        return False
    except TelegramAPIError as error:
        log.error(error)
        await message.reply(
            f"🤷‍♂️ I'm sorry {message.from_user.username}, I'm afraid I can't do that."
        )
        return False
    finally:
        await info_message.delete()
        if downloaded:
            downloaded.close()
            os.remove(downloaded.name)
        if slowed_down:
            os.remove(slowed_down)