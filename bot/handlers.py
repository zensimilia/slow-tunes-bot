import os

from aiogram import Dispatcher, types

from bot import db
from bot.config import AppConfig
from bot.utils import audio

config = AppConfig()


def register_handlers(dp: Dispatcher):
    """Register all the Bot's handlers."""

    dp.register_message_handler(command_start, commands=["start", "help"])
    dp.register_message_handler(
        proceed_audio,
        content_types=[types.ContentType.AUDIO],
    )
    dp.register_message_handler(answer_message)


async def proceed_audio(message: types.Message):
    """Slow down uploaded audio track and send it to user."""

    # Check if audio is already slowed then return it from telegram servers
    from_db = await db.get_match(message.audio.file_unique_id)
    if from_db:
        await message.reply_audio(from_db[2], caption="@slowtunesbot")
        return

    temp_file = os.path.join(
        config.DATA_DIR, f'{message.audio.file_unique_id}.bin'
    )
    await message.audio.download(destination_file=temp_file)
    await types.ChatActions.record_audio()
    slowed_down = await audio.slow_down(temp_file, config.SPEED_RATIO)
    os.remove(temp_file)

    if slowed_down:
        await types.ChatActions.upload_audio()
        new_file_name = (
            f'{os.path.splitext(message.audio.file_name)[0]} @slowtunesbot.mp3'
        )
        reply = await message.reply_audio(
            types.InputFile(slowed_down, filename=new_file_name),
            caption="@slowtunesbot",
        )
        os.remove(slowed_down)
        await db.insert_match(
            message.audio.file_unique_id,
            reply.audio.file_id,
        )
        return

    await types.ChatActions.typing()
    await message.reply('Sorry!')


async def answer_message(message: types.Message):
    """Handler for debug incoming messages."""

    await message.answer("Throw an audio. I'll catch!")


async def command_start(message: types.Message):
    """Handler for `/start` command."""

    await message.answer("Send me the audio track " "and i will...")
