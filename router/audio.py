import asyncio

from aiogram import F, Router, flags, types

from core.queue import TaskQueue
from db.base import Database

audio_router = Router()


@audio_router.message(F.audio)
@flags.rate_limit(rate=3, key="audio")
async def audio_handler(message: types.Message, db: Database, queue: TaskQueue):
    # Example of enqueuing a task
    async def process_audio():
        await message.answer("Audio received! Processing...")
        # Simulate audio processing
        await asyncio.sleep(10)
        await message.answer("Audio processing complete!")

    queue.enqueue(process_audio)
