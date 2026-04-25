from pathlib import Path

from aiogram import F, Router, flags, types
from aiogram.exceptions import TelegramAPIError

from core.exceptions import DownloadError, FileIsTooBig, NoAudio
from core.messages import QUEUE_POSITION_TEXT
from core.queue import TaskQueue
from db.base import Database
from keyboards.public import please_wait_button
from utils.sox import SoxException, proceed_audio
from utils.tg import download_file_to_buffer, get_caption_mention

audio_router = Router()

AUDIO_SIZE_LIMIT = 20 * 1024 * 1024  # 20 MB


@audio_router.message(F.audio)
@flags.rate_limit(rate=3, key="audio")
async def audio_handler(message: types.Message, db: Database, queue: TaskQueue) -> None:
    if not message.audio:
        raise NoAudio("No audio file found in the message")

    file_size = message.audio.file_size
    if file_size and file_size >= AUDIO_SIZE_LIMIT:
        raise FileIsTooBig(f"Audio file is too big: {file_size} bytes. Limit is {AUDIO_SIZE_LIMIT} bytes")

    task = queue.enqueue(slowing_down_task, message)

    if task > 1:
        await message.reply(QUEUE_POSITION_TEXT.format(task=task), disable_notification=True)


async def slowing_down_task(message: types.Message) -> None:
    if not message.bot:
        return

    if not message.audio or not message.audio.file_name:
        raise NoAudio(f"No audio file found in the message #{message.message_id}")

    info_message = await message.reply(
        "💿 Start slowing down...",
        disable_notification=True,
        reply_markup=please_wait_button(),
    )

    slowed_filename = f"{Path(message.audio.file_name).stem}_slowed.mp3"

    try:
        buffer_audio = await download_file_to_buffer(message.bot, message.audio.file_id)
        slowed_audio = await proceed_audio(buffer_audio)
        upload_audio = types.BufferedInputFile(slowed_audio, filename=slowed_filename)
    except TelegramAPIError as err:
        raise DownloadError(f"Failed to download/upload audio file: {err}") from err
    except SoxException as err:
        raise Exception(f"Failed to process audio file: {err}") from err

    slowed = await message.reply_audio(
        audio=upload_audio,
        message_effect_id="5104841245755180586",
        title=f"{message.audio.title} (Slowed)",
        performer=message.audio.performer,
        caption=await get_caption_mention(message.bot),
    )
    await info_message.delete()
