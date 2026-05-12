from typing import TYPE_CHECKING

from aiogram import F, Router, flags, types

from bot import messages as txt
from bot.core.exceptions import FileIsTooBigError
from bot.handlers.tasks import slowing_down_task
from bot.keyboards.cbd import MatchAction, MatchCbd
from bot.utils import tg

if TYPE_CHECKING:
    from bot.services.queue import TaskQueue
    from db.engine import Database
    from db.models.user import User
    from db.repository.master import MasterStorage

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 Mb

audio_router = Router()


@audio_router.message(F.audio.as_("audio"))
@flags.rate_limit(rate=3, key="audio_handler")
async def audio_handler(  # noqa: PLR0913
    message: types.Message,
    queue: TaskQueue,
    user: User,
    storage: MasterStorage,
    audio: types.Audio,
    db: Database,
) -> None:
    if not message.bot:
        return

    if audio.file_size and audio.file_size >= MAX_FILE_SIZE:
        raise FileIsTooBigError(audio.file_size)

    if saved_match := await storage.match.get_by_original_id(audio.file_id):
        reply_markup = MatchCbd(action=MatchAction.NONE, pk=saved_match.pk).get_keyboard(
            is_private=saved_match.is_private,
            is_owner=user.pk == saved_match.user_pk,
            is_random=False,
        )
        await tg.reply_audio(saved_match.slowed_id, message, reply_markup=reply_markup)
    else:
        queue.enqueue(slowing_down_task, message, db, user.pk)
        if (position := queue.total_pending) > 1:
            text = txt.QUEUE_POSITION_TEXT.format(position=position)
            await message.reply(text, disable_notification=True)


@audio_router.callback_query(MatchCbd.filter(F.action == MatchAction.SHARE))
@flags.rate_limit(rate=3, key="share_handler")
async def share_handler(callback: types.CallbackQuery, callback_data: MatchCbd) -> None:
    if isinstance(callback.message, types.Message):
        reply_markup = callback_data.get_keyboard(is_owner=True, is_private=True, is_liked=False)
        await callback.message.edit_reply_markup(reply_markup=reply_markup)
    else:
        callback.answer("Something went wrong!", show_alert=True)
