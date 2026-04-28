from aiogram import types
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.utils.chat_action import ChatActionSender

from core import messages as txt
from core.exceptions import DownloadError, FileIsTooBig, UploadError
from db.base import Database
from db.exceptions import DoesNotExist
from db.match import create_match, get_match_by_original_id
from db.schemas import NewMatch
from utils import sox, tg


async def slowing_down_task(message: types.Message, db: Database, user_pk: int) -> None:
    if not message.bot or not message.from_user:  # hello Optional
        return
    if not message.audio or not message.audio.file_name:  # hello fucking Optional
        return

    fmt = tg.get_audio_file_extension(message.audio)
    if fmt not in (sox.SUPPORTED_FMT):
        await message.reply(txt.UNSUPPORTED_FMT, disable_notification=True)
        return

    try:  # send already slowed audio if it exists
        if saved_match := await db.execute(get_match_by_original_id, message.audio.file_id):
            await tg.reply_audio(saved_match.slowed_id, message)
            return
    except DoesNotExist:
        pass  # this is expected behavior
    except (TelegramAPIError, ValueError) as err:
        raise UploadError(f"Failed to upload audio file: {err}") from err

    async with tg.temp_message(txt.START_SLOWING_DOWN, message):
        try:  # download the audio
            buffer_audio = await tg.download_file_to_buffer(message.bot, message.audio.file_id)
        except TelegramBadRequest as err:
            await message.reply(txt.FILE_IS_TOO_BIG, disable_notification=True)
            raise FileIsTooBig("File is too big") from err
        except TelegramAPIError as err:
            raise DownloadError(f"Failed to download audio file: {err}") from err

        try:  # slow down the audio
            async with ChatActionSender.record_voice(bot=message.bot, chat_id=message.chat.id):
                slowed_audio = await sox.proceed_audio(buffer_audio, fmt)
        except sox.SoxException as err:
            del slowed_audio
            raise Exception(f"Failed to process audio file: {err}") from err
        finally:
            buffer_audio.close()
            del buffer_audio

        try:  # upload the slowed audio file to the user
            async with ChatActionSender.upload_voice(bot=message.bot, chat_id=message.chat.id):
                slowed_filename = await tg.get_filename_mention(message.bot, message.audio.file_name)
                upload_audio = types.BufferedInputFile(slowed_audio, filename=slowed_filename)
                slowed_message = await tg.reply_audio(upload_audio, message)
        except (TelegramAPIError, OSError, ValueError) as err:
            raise UploadError(f"Failed to upload audio file: {err}") from err
        finally:
            del slowed_audio

    if slowed_message.audio:  # save the match to the database
        new_match = NewMatch(
            original_id=message.audio.file_id,
            slowed_id=slowed_message.audio.file_id,
            user_pk=user_pk,
            private=True,
            forbidden=False,
        )
        await db.execute(create_match, new_match)
