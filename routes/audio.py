from typing import TYPE_CHECKING

from aiogram import F, Router, flags, types

from core.messages import QUEUE_POSITION_TEXT
from handlers.tasks import slowing_down_task

if TYPE_CHECKING:
    from core.queue import TaskQueue
    from storage.match import MatchStore
    from storage.user import UserStore

audio_router = Router()


@audio_router.message(F.audio.as_("audio"))
@flags.rate_limit(rate=3, key="audio")
async def audio_handler(
    message: types.Message,
    queue: TaskQueue,
    # user: UserRead,
    match_store: MatchStore,
    user_store: UserStore,
) -> None:
    if not message.from_user:
        return

    user = await user_store.get_by(tg_id=message.from_user.id)
    queue.enqueue(slowing_down_task, message, match_store, user.pk)

    position = queue.total_pending
    if position > 1:
        await message.reply(QUEUE_POSITION_TEXT.format(position=position), disable_notification=True)
