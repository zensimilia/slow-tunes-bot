from typing import TYPE_CHECKING

from aiogram import types
from aiogram.exceptions import TelegramAPIError
from aiogram.utils.chat_action import ChatActionSender
from core import messages as txt
from core.exceptions import UploadError
from keyboards.cbd import MatchAction, MatchCbd
from services.audio_processor import AudioProcessor
from services.sox import SoxCommandBuilder
from utils import tg

from db.models.match import MatchNew

if TYPE_CHECKING:
    from db.storage.match import MatchStore

OUTPUT_MP3_QUALITY = "320"  # best CBR
CHUNK_SIZE = 64 * 1024  # 64 kb
PIPE_ERROR_MSG = "Process was created without stdin or stderr PIPE"


async def proceed_audio(file_url: str) -> bytes:
    fmt = tg.get_file_fmt_from_url(file_url)
    sox_command = (
        SoxCommandBuilder(input_format=fmt, output_quality=OUTPUT_MP3_QUALITY)
        .gain(-3)
        .speed(33 / 45)
        .filters(highpass_freq=100, lowpass_freq=15000)
        .padding(0, 2)
        .reverb(reverberance=70, hf_damping=50, scale=100, stereo_depth=100)
        .bass(3)
        .normalize(-1)
        .dither()
    )

    audio_processor = AudioProcessor(sox_command)

    return await audio_processor.process_url(file_url)


async def slowing_down_task(message: types.Message, match_store: MatchStore, user_pk: int) -> None:
    audio = tg.get_audio(message)
    bot = tg.get_bot(message)

    file_obj = await bot.get_file(audio.file_id)
    file_url = tg.get_file_download_url(file_obj)

    async with tg.temp_message(txt.START_SLOWING_DOWN, message):
        async with ChatActionSender.record_voice(bot=bot, chat_id=message.chat.id):
            slowed_audio = await proceed_audio(file_url)

        new_match = MatchNew(
            original_id=audio.file_id,
            slowed_id=str(0),
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


async def send_match_if_exist(message: types.Message, match_store: MatchStore) -> bool:
    if not message.audio:
        return False
    cb = MatchCbd(action=MatchAction.NONE)
    if saved_match := await match_store.get_by_original_id(message.audio.file_id):
        reply_markup = cb.get_keyboard(
            match_pk=saved_match.pk or 0,
            is_private=saved_match.is_private,
            is_owner=True,
            is_random=False,
        )
        await tg.reply_audio(saved_match.slowed_id, message, reply_markup=reply_markup)
        return True
    return False


def get_audiofile_format(audio: types.Audio) -> str:
    return tg.get_audio_file_extension(audio)
