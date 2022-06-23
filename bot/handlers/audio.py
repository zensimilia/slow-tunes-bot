import os

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import FileIsTooBig, TelegramAPIError

from bot import db, keyboards
from bot.config import AppConfig
from bot.utils import audio
from bot.utils.brand import get_branded_file_name, get_caption
from bot.utils.logger import get_logger
from bot.utils.queue import Queue
from bot.utils.exceptions import QueueLimitReached

config = AppConfig()
queue = Queue()
log = get_logger()


async def processing_audio(message: types.Message, state: FSMContext):
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

    async with state.proxy() as data:
        in_queue = data.get("in_queue", 0)
        if in_queue >= 3:
            raise QueueLimitReached("User has reached the limit in the queue")

        # Add slowing down audio task to the queue
        queue.enqueue(slowing_down_task, message, state)

        data.update(in_queue=in_queue + 1)

    if queue.size > 1:
        await message.reply(
            f"🕙 Added your request to the queue. Your position: {queue.size}.",
            disable_notification=True,
        )


async def slowing_down_task(message: types.Message, state: FSMContext) -> bool:
    """Slowing down audio Task."""

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
        downloaded.close()

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
                "Please send me another file or try again later."
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
            os.remove(downloaded.name)
        if slowed_down:
            os.remove(slowed_down)
        async with state.proxy() as data:
            in_queue = data.get("in_queue", 1)
            data.update(in_queue=in_queue - 1)
