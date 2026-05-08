from typing import TYPE_CHECKING

import aiohttp
from aiogram import types
from aiogram.exceptions import TelegramAPIError
from aiogram.utils.chat_action import ChatActionSender

from bot import messages as txt
from bot.core.exceptions import UploadError
from bot.keyboards.cbd import MatchAction, MatchCbd
from bot.services.audio_processor import AudioProcessor
from bot.services.ffmpeg import FFmpegCommandBuilder
from bot.utils import tg
from db.models.match import MatchNew

if TYPE_CHECKING:
    from db.repository.match import MatchStore

OUTPUT_MP3_QUALITY = 320
SAMPLE_RATE = 48000
CHUNK_SIZE = 64 * 1024  # 64 kb


async def proceed_audio(file_url: str) -> bytes:
    ffmpeg_command = (
        FFmpegCommandBuilder(bitrate=OUTPUT_MP3_QUALITY, sample_rate=SAMPLE_RATE)
        .speed(33 / 45)
        .reverb(intensity=0.5, extrastereo=False)
    )
    audio_processor = AudioProcessor(ffmpeg_command)
    async with aiohttp.ClientSession() as session:
        return await audio_processor.process_url(file_url, session=session)


async def slowing_down_task(message: types.Message, match_store: MatchStore, user_pk: int) -> None:
    audio = tg.get_audio(message)
    bot = tg.get_bot(message)

    async with tg.temp_message(txt.START_SLOWING_DOWN, message):
        file_obj = await bot.get_file(audio.file_id)
        file_url = tg.get_file_download_url(file_obj)

        async with ChatActionSender.record_voice(bot=bot, chat_id=message.chat.id):
            slowed_audio = await proceed_audio(file_url)

        new_match = MatchNew(
            original_id=audio.file_id,
            user_pk=user_pk,
            is_private=True,
            is_forbidden=False,
        )
        cb = MatchCbd(action=MatchAction.NONE)
        reply_markup = cb.get_keyboard(
            match_pk=0,
            is_private=new_match.is_private,
            is_owner=True,
            is_liked=False,
            is_random=False,
        )

        async with ChatActionSender.upload_voice(bot=bot, chat_id=message.chat.id):
            try:  # upload the slowed audio file to the user
                slowed_filename = await tg.get_filename_mention(bot, audio.file_name or audio.file_id)
                input_audio_file = types.BufferedInputFile(slowed_audio, filename=slowed_filename)
                upload_message = await tg.reply_audio(input_audio_file, message, reply_markup=reply_markup)
            except (TelegramAPIError, OSError, ValueError) as err:
                raise UploadError from err

    if upload_message.audio:  # save the match to the database
        new_match.slowed_id = upload_message.audio.file_id
        await match_store.create(new_match)
