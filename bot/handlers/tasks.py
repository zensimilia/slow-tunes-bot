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
from bot.utils.enums import FxAnalog, FxFilter, FxReverb
from models import Match

if TYPE_CHECKING:
    from aiogram.client.session.aiohttp import AiohttpSession

    from models.user import UserOptions


OUTPUT_MP3_QUALITY = 320
SAMPLE_RATE = 48000
CHUNK_SIZE = 64 * 1024  # 64 kb


async def proceed_audio(file_url: str, *, session: AiohttpSession, options: UserOptions) -> bytes:
    ffmpeg_command = FFmpegCommandBuilder(bitrate=OUTPUT_MP3_QUALITY, sample_rate=SAMPLE_RATE).speed(33.3 / 45)
    match options.fx_reverb:
        case FxReverb.NORMAL:
            ffmpeg_command = ffmpeg_command.reverb(intensity=0.2)
        case FxReverb.EXTREME:
            ffmpeg_command = ffmpeg_command.reverb(intensity=0.6)
    match options.fx_filter:
        case FxFilter.LOFI:
            ffmpeg_command = ffmpeg_command.filters(lowpass_freq=6000, highpass_freq=300, master=True)
        case FxFilter.RADIO:
            ffmpeg_command = ffmpeg_command.filters(lowpass_freq=4000, highpass_freq=600, master=True)
        case FxFilter.TELEPHONE:
            ffmpeg_command = ffmpeg_command.filters(lowpass_freq=3000, highpass_freq=800, master=True)
    if options.fx_analog is not FxAnalog.NONE:
        ffmpeg_command = ffmpeg_command.analog(options.fx_analog)
        ffmpeg_command = ffmpeg_command.flutter(depth=0.20, freq=60 / 33.3)
        ffmpeg_command = ffmpeg_command.softclip()
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


async def slowing_down_task(message: types.Message, options: UserOptions) -> None:
    audio = tg.get_audio(message)
    bot = tg.get_bot(message)
    session = tg.get_session(message)

    async with tg.temp_message(txt.START_SLOWING_DOWN, message):
        async with ChatActionSender.record_voice(bot=bot, chat_id=message.chat.id):
            file_obj = await bot.get_file(audio.file_id)
            file_url = tg.get_file_download_url(file_obj)
            slowed_audio = await proceed_audio(file_url, session=session, options=options)

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
