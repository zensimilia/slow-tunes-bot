from pathlib import Path

from aiogram import F, Router, flags, types
from aiogram.exceptions import TelegramAPIError
from aiogram.utils.chat_action import ChatActionSender

from core.exceptions import DownloadError, FileIsTooBig, UploadError
from core.messages import QUEUE_POSITION_TEXT
from core.queue import TaskQueue
from db.base import Database
from db.match import create_match, get_match_by_original_id
from db.schemas import GetUser, NewMatch
from keyboards.public import please_wait_button
from utils.sox import SoxException, proceed_audio
from utils.tg import download_file_to_buffer, get_caption_mention

audio_router = Router()

AUDIO_SIZE_LIMIT = 20 * 1024 * 1024  # 20 MB


@audio_router.message(F.audio.as_("audio"))
@flags.rate_limit(rate=3, key="audio")
async def audio_handler(
    message: types.Message,
    db: Database,
    queue: TaskQueue,
    user: GetUser,
    audio: types.Audio,
) -> None:
    file_size = audio.file_size
    if file_size and file_size >= AUDIO_SIZE_LIMIT:
        raise FileIsTooBig(f"Audio file is too big: {file_size} bytes. Limit is {AUDIO_SIZE_LIMIT} bytes")

    task = queue.enqueue(slowing_down_task, message, db, user)

    if task > 1:
        await message.reply(QUEUE_POSITION_TEXT.format(task=task), disable_notification=True)


async def slowing_down_task(message: types.Message, db: Database, user: GetUser) -> None:
    if not message.bot or not message.from_user:  # hello Optional
        return
    if not message.audio or not message.audio.file_name:  # hello fucking Optional
        return

    try:  # send already slowed audio if it exists
        if saved_match := await db.execute(get_match_by_original_id, message.audio.file_id):
            await reply_audio(saved_match.slowed_id, message)
            return
    except (TelegramAPIError, ValueError) as err:
        raise UploadError(f"Failed to upload audio file: {err}") from err

    info_message = await message.reply(
        "💿 Start slowing down...",
        disable_notification=True,
        reply_markup=please_wait_button(),
    )

    try:  # download and slow down the audio file
        async with ChatActionSender.record_voice(bot=message.bot, chat_id=message.chat.id):
            buffer_audio = await download_file_to_buffer(message.bot, message.audio.file_id)
            slowed_audio = await proceed_audio(buffer_audio)
    except TelegramAPIError as err:
        raise DownloadError(f"Failed to download audio file: {err}") from err
    except SoxException as err:
        raise Exception(f"Failed to process audio file: {err}") from err

    try:  # upload the slowed audio file to the user
        async with ChatActionSender.upload_voice(bot=message.bot, chat_id=message.chat.id):
            slowed_filename = f"{Path(message.audio.file_name).stem}_slowed.mp3"
            upload_audio = types.BufferedInputFile(slowed_audio, filename=slowed_filename)
            slowed = await reply_audio(upload_audio, message)
    except (TelegramAPIError, OSError, ValueError) as err:
        raise UploadError(f"Failed to upload audio file: {err}") from err
    finally:
        await info_message.delete()

    if slowed.audio:  # save the match to the database
        new_match = NewMatch(
            original_id=message.audio.file_id,
            slowed_id=slowed.audio.file_id,
            user_pk=user.pk,
        )
        await db.execute(create_match, new_match)


async def reply_audio(audio: types.InputFileUnion, message: types.Message, effect: bool = True) -> types.Message:
    if not message.bot or not message.audio:  # hello fucking fucking Optional
        raise ValueError("There is no required objects in the Message")

    return await message.reply_audio(
        audio=audio,
        message_effect_id="5104841245755180586" if effect else None,
        title=f"{message.audio.title} (Slowed)",
        performer=message.audio.performer,
        caption=await get_caption_mention(message.bot),
    )
