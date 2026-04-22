import asyncio

from aiogram import F, Router, types

from core.queue import TaskQueue
from db.base import Database

audio_router = Router()


async def audio_handler(message: types.Message, db: Database, queue: TaskQueue):
    # Example of enqueuing a task
    async def process_audio():
        await message.answer("Audio received! Processing...")
        # Simulate audio processing
        await asyncio.sleep(10)
        await message.answer("Audio processing complete!")

    queue.enqueue(process_audio)


audio_router.message.register(audio_handler, F.audio)
