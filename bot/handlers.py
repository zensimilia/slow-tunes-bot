from aiogram import Dispatcher, types

from bot.config import AppConfig
from bot.utils import audio

config = AppConfig()


def register_handlers(dp: Dispatcher):
    """Register all the Bot's handlers."""

    dp.register_message_handler(command_start, commands=["start", "help"])
    dp.register_message_handler(
        proceed_audio,
        content_types=[types.ContentType.VOICE, types.ContentType.AUDIO],
    )
    dp.register_message_handler(debug_message)


async def proceed_audio(message: types.Message):
    """Slow down the audio track or voice message."""

    message_type = message.content_type
    file_obj = await message[message_type].get_file()
    file_dest = f'{config.DATA_DIR}{file_obj.file_path}'
    await message[message_type].download(destination_file=file_dest)
    await types.ChatActions.upload_audio()
    slowed_down = await audio.slow_down(file_dest, config.SPEED_RATIO)
    if slowed_down:
        await message.reply_audio(types.InputFile(slowed_down))
        return
    await types.ChatActions.typing()
    await message.reply(file_obj)


async def debug_message(message: types.Message):
    """Handler for debug incoming messages."""

    allowed_content_types = ("audio", "photo", "video", "text")

    if message.content_type not in allowed_content_types:
        return


async def command_start(message: types.Message):
    """Handler for `/start` command."""

    await message.answer(
        "Привет, дорогой друг! "
        "Ты не найдешь тут ничего интересного. "
        "Всё скрыто в чертогах цифрового разума. "
        "Будь умницей. Не тупи. "
        "Бип! Боп! 🤖"
    )
