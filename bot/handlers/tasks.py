from typing import TYPE_CHECKING

from aiogram import types
from aiogram.exceptions import TelegramAPIError
from aiogram.utils.chat_action import ChatActionSender

from bot import messages as txt
from bot.core.exceptions import UploadError
from bot.keyboards.cbd import MatchAction, MatchCbd
from bot.services.audio_processor import AudioProcessor
from bot.services.ffmpeg import FFmpegCommandBuilder
from bot.utils import tg
from bot.utils.enums import FxAnalog
from models import Match

if TYPE_CHECKING:
    from aiogram.client.session.aiohttp import AiohttpSession


OUTPUT_MP3_QUALITY = 320
SAMPLE_RATE = 44100
CHUNK_SIZE = 64 * 1024  # 64 kb


async def proceed_audio(file_url: str, *, session: AiohttpSession) -> bytes:
    ffmpeg_command = (
        FFmpegCommandBuilder(bitrate=OUTPUT_MP3_QUALITY, sample_rate=SAMPLE_RATE)
        .filters(lowpass_freq=10000, highpass_freq=200)
        .speed(33.3 / 45)
        .reverb(intensity=0.1)
        .analog(FxAnalog.TAPE, weight=0.5)
        .flutter(master=True, depth=0.25, freq=60 / 33.3)
        .softclip(master=True)
    )
    client = await session.create_session()
    audio_processor = AudioProcessor(ffmpeg_command)
    return await audio_processor.process_url(file_url, session=client)


async def upload_audio(data: bytes, filename: str, message: types.Message) -> types.Message:
    try:
        input_audio_file = types.BufferedInputFile(data, filename=filename)
        return await tg.reply_audio(input_audio_file, message)
    except (TelegramAPIError, OSError, ValueError) as err:
        raise UploadError from err


async def save_audio_to_db(original_id: str, slowed_id: str, message: types.Message) -> Match:
    new_match = Match(
        original_id=original_id,
        slowed_id=slowed_id,
        tg_user_id=message.chat.id,
        is_private=True,
        is_forbidden=False,
    )
    await new_match.save()
    return new_match


async def slowing_down_task(message: types.Message) -> None:
    audio = tg.get_audio(message)
    bot = tg.get_bot(message)
    session = tg.get_session(message)

    async with tg.temp_message(txt.START_SLOWING_DOWN, message):
        async with ChatActionSender.record_voice(bot=bot, chat_id=message.chat.id):
            file_obj = await bot.get_file(audio.file_id)
            file_url = tg.get_file_download_url(file_obj)
            slowed_audio = await proceed_audio(file_url, session=session)

        async with ChatActionSender.upload_voice(bot=bot, chat_id=message.chat.id):
            slowed_filename = await tg.get_filename_mention(bot, audio.file_name or audio.file_id)
            upload_message = await upload_audio(slowed_audio, slowed_filename, message)

    if upload_message.audio:
        match = await save_audio_to_db(audio.file_id, upload_message.audio.file_id, message)
        reply_markup = MatchCbd(action=MatchAction.NONE, pk=match.pk).get_keyboard(
            is_private=match.is_private,
            is_owner=True,
            is_random=False,
        )
        await upload_message.edit_reply_markup(reply_markup=reply_markup)
