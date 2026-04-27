from aiogram import F, Router, flags, types

from core.messages import QUEUE_POSITION_TEXT
from core.queue import TaskQueue
from db.base import Database
from db.schemas import GetUser
from handlers.tasks import slowing_down_task

audio_router = Router()


@audio_router.message(F.audio.as_("audio"))
@flags.rate_limit(rate=3, key="audio")
async def audio_handler(
    message: types.Message,
    db: Database,
    queue: TaskQueue,
    user: GetUser,
) -> None:
    task = queue.enqueue(slowing_down_task, message, db, user.pk)

    if task > 1:
        await message.reply(QUEUE_POSITION_TEXT.format(task=task), disable_notification=True)
