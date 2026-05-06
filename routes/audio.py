from typing import TYPE_CHECKING

from aiogram import F, Router, flags, types

from core.exceptions import FileIsTooBigError
from core.messages import QUEUE_POSITION_TEXT
from handlers.tasks import send_match_if_exist, slowing_down_task
from keyboards.cbd import MatchAction, MatchCbd

if TYPE_CHECKING:
    from core.queue import TaskQueue
    from models.user import User
    from storage.match import MatchStore

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 Mb

audio_router = Router()


@audio_router.message(F.audio.as_("audio"))
@flags.rate_limit(rate=3, key="audio_handler")
async def audio_handler(
    message: types.Message,
    queue: TaskQueue,
    user: User,
    match_store: MatchStore,
    audio: types.Audio,
) -> None:
    if audio.file_size and audio.file_size >= MAX_FILE_SIZE:
        raise FileIsTooBigError

    if await send_match_if_exist(message, match_store):
        return

    queue.enqueue(slowing_down_task, message, match_store, user.pk)

    position = queue.total_pending
    if position > 1:
        await message.reply(QUEUE_POSITION_TEXT.format(position=position), disable_notification=True)


@audio_router.callback_query(MatchCbd.filter(F.action == MatchAction.SHARE))
@flags.rate_limit(rate=3, key="share_handler")
async def share_handler(callback: types.CallbackQuery, callback_data: MatchCbd) -> None:
    if isinstance(callback.message, types.Message):
        reply_markup = callback_data.get_keyboard(match_pk=0, is_owner=True, is_private=True, is_liked=False)
        await callback.message.edit_reply_markup(reply_markup=reply_markup)
    else:
        callback.answer("Something went wrong!", show_alert=True)
