from typing import TYPE_CHECKING

from aiogram import types
from aiogram.exceptions import TelegramAPIError
from aiogram.utils.chat_action import ChatActionSender

from core import messages as txt
from core.exceptions import DownloadError, UnsupportedFormatError, UploadError
from models.match import MatchNew
from utils import sox, tg

if TYPE_CHECKING:
    from storage.match import MatchStore

OUTPUT_MP3_QUALITY = "-0.9"  # VBR


async def slowing_down_task(message: types.Message, match_store: MatchStore, user_pk: int, fmt: str) -> None:
    if not message.bot or not message.from_user:  # hello Optional
        return
    if not message.audio or not message.audio.file_name:  # hello fucking Optional
        return

    sox_command = (
        sox
        .SoxCommandBuilder(input_format=fmt, output_quality=OUTPUT_MP3_QUALITY)
        .speed(33 / 45)
        .padding(0, 2)
        .gain(-3)
        .reverb(reverberance=70, hf_damping=30, scale=100, stereo_depth=50)
        .filters(highpass_freq=50)
        .bass(3)
        .normalize(-1)
        .build_list()
    )

    async with tg.temp_message(txt.START_SLOWING_DOWN, message):
        try:  # download the audio
            buffer_audio = await tg.download_file_to_buffer(message.bot, message.audio.file_id)
        except TelegramAPIError as err:
            raise DownloadError from err

        try:  # slow down the audio
            async with ChatActionSender.record_voice(bot=message.bot, chat_id=message.chat.id):
                slowed_audio = await sox.proceed_audio(buffer_audio, sox_command)
        except sox.SoxError as err:
            del slowed_audio
            raise DownloadError from err
        finally:
            buffer_audio.close()
            del buffer_audio

        try:  # upload the slowed audio file to the user
            async with ChatActionSender.upload_voice(bot=message.bot, chat_id=message.chat.id):
                slowed_filename = await tg.get_filename_mention(message.bot, message.audio.file_name)
                upload_audio = types.BufferedInputFile(slowed_audio, filename=slowed_filename)
                slowed_message = await tg.reply_audio(upload_audio, message)
        except (TelegramAPIError, OSError, ValueError) as err:
            raise UploadError from err
        finally:
            del slowed_audio

    if slowed_message.audio:  # save the match to the database
        new_match = MatchNew(
            original_id=message.audio.file_id,
            slowed_id=slowed_message.audio.file_id,
            user_pk=user_pk,
            is_private=True,
            is_forbidden=False,
        )
        await match_store.create(new_match)


async def send_match_if_exist(message: types.Message, match_store: MatchStore) -> bool:
    if not message.audio:
        return False
    if saved_match := await match_store.get_by_original_id(message.audio.file_id):
        await tg.reply_audio(saved_match.slowed_id, message)
        return True
    return False


def get_audiofile_format(audio: types.Audio) -> str:
    return tg.get_audio_file_extension(audio)


def is_format_supported(fmt: str) -> bool:
    return sox.is_supported_format(fmt)
