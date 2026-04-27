from pathlib import Path

from aiogram import types
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.utils.chat_action import ChatActionSender

from core import messages as txt
from core.exceptions import DownloadError, FileIsTooBig, UploadError
from db.base import Database
from db.exceptions import DoesNotExist
from db.match import create_match, get_match_by_original_id
from db.schemas import NewMatch
from utils.sox import SoxException, proceed_audio
from utils.tg import download_file_to_buffer, reply_audio, temp_message


async def slowing_down_task(message: types.Message, db: Database, user_pk: int) -> None:
    if not message.bot or not message.from_user:  # hello Optional
        return
    if not message.audio or not message.audio.file_name:  # hello fucking Optional
        return

    try:  # send already slowed audio if it exists
        if saved_match := await db.execute(get_match_by_original_id, message.audio.file_id):
            await reply_audio(saved_match.slowed_id, message)
            return
    except DoesNotExist:
        pass
    except (TelegramAPIError, ValueError) as err:
        raise UploadError(f"Failed to upload audio file: {err}") from err

    async with temp_message(txt.START_SLOWING_DOWN, message) as _:
        try:  # download and slow down the audio file
            async with ChatActionSender.record_voice(bot=message.bot, chat_id=message.chat.id):
                buffer_audio = await download_file_to_buffer(message.bot, message.audio.file_id)
                slowed_audio = await proceed_audio(buffer_audio)
        except TelegramBadRequest as err:
            await message.reply(txt.FILE_IS_TOO_BIG, disable_notification=True)
            raise FileIsTooBig("File is too big") from err
        except TelegramAPIError as err:
            raise DownloadError(f"Failed to download audio file: {err}") from err
        except SoxException as err:
            raise Exception(f"Failed to process audio file: {err}") from err

        slowed_filename = f"{Path(message.audio.file_name).stem}_slowed.mp3"

        try:  # upload the slowed audio file to the user
            async with ChatActionSender.upload_voice(bot=message.bot, chat_id=message.chat.id):
                upload_audio = types.BufferedInputFile(slowed_audio, filename=slowed_filename)
                slowed = await reply_audio(upload_audio, message)
        except (TelegramAPIError, OSError, ValueError) as err:
            raise UploadError(f"Failed to upload audio file: {err}") from err

    if slowed.audio:  # save the match to the database
        new_match = NewMatch(
            original_id=message.audio.file_id,
            slowed_id=slowed.audio.file_id,
            user_pk=user_pk,
        )
        await db.execute(create_match, new_match)
