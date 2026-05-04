from typing import TYPE_CHECKING

from aiogram import F, Router, flags, types

from core.exceptions import FileIsTooBigError, UnsupportedFormatError
from core.messages import QUEUE_POSITION_TEXT
from handlers.tasks import get_audiofile_format, is_format_supported, send_match_if_exist, slowing_down_task

if TYPE_CHECKING:
    from core.queue import TaskQueue
    from models.user import User
    from storage.match import MatchStore

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 Mb

audio_router = Router()


@audio_router.message(F.audio.as_("audio"))
@flags.rate_limit(rate=3, key="audio")
async def audio_handler(
    message: types.Message,
    queue: TaskQueue,
    user: User,
    match_store: MatchStore,
    audio: types.Audio,
) -> None:
    if audio.file_size and audio.file_size >= MAX_FILE_SIZE:
        raise FileIsTooBigError

    fmt = get_audiofile_format(audio)
    if not is_format_supported(fmt):
        raise UnsupportedFormatError

    if await send_match_if_exist(message, match_store):
        return

    queue.enqueue(slowing_down_task, message, match_store, user.pk)

    position = queue.total_pending
    if position > 1:
        await message.reply(QUEUE_POSITION_TEXT.format(position=position), disable_notification=True)
