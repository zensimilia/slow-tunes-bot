import asyncio
from typing import TYPE_CHECKING

import aiohttp
from aiogram import types
from aiogram.exceptions import TelegramAPIError
from aiogram.utils.chat_action import ChatActionSender

from core import messages as txt
from core.exceptions import DownloadError, UploadError
from models.match import MatchNew
from utils import sox, tg

if TYPE_CHECKING:
    from asyncio.subprocess import Process

    from storage.match import MatchStore

OUTPUT_MP3_QUALITY = "-0"  # best VBR
CHUNK_SIZE = 64 * 1024  # 64 kb
PIPE_ERROR_MSG = "Process was created without stdin or stderr PIPE"


async def feed_process(process: Process, file_url: str) -> None:
    if not process.stdin or not process.stderr:
        raise RuntimeError(PIPE_ERROR_MSG)
    try:
        async with aiohttp.ClientSession() as s:
            resp = await s.get(file_url)
            resp.raise_for_status()
            async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                process.stdin.write(chunk)
                await process.stdin.drain()
    except aiohttp.ClientResponseError as err:
        raise DownloadError from err
    except (BrokenPipeError, ConnectionResetError) as err:
        raw_errors = await process.stderr.read()
        if raw_errors:
            raise sox.SoxError(raw_errors.decode()) from err
        raise RuntimeError from err
    finally:
        if process.stdin:
            process.stdin.close()
            await process.stdin.wait_closed()


async def read_process(process: Process) -> bytes:
    if not process.stdout:
        raise RuntimeError(PIPE_ERROR_MSG)
    return await process.stdout.read()


async def slowing_down_task(message: types.Message, match_store: MatchStore, user_pk: int, fmt: str) -> None:
    if not message.bot or not message.from_user:  # hello Optional
        return
    if not message.audio or not message.audio.file_name:  # hello fucking Optional
        return

    file = await message.bot.get_file(message.audio.file_id)
    file_url = tg.get_file_download_url(file)

    sox_command = (
        sox
        .SoxCommandBuilder(input_format=fmt, output_quality=OUTPUT_MP3_QUALITY)
        .speed(33 / 45)
        .padding(0, 2)
        .gain(-3)
        .reverb(reverberance=70, hf_damping=50, scale=100, stereo_depth=100)
        .filters(highpass_freq=50)
        .bass(3)
        .normalize(-1)
        .build_list()
    )

    process = await asyncio.create_subprocess_exec(
        *sox_command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async with tg.temp_message(txt.START_SLOWING_DOWN, message):
        async with ChatActionSender.record_voice(bot=message.bot, chat_id=message.chat.id):
            _, processed_audio = await asyncio.gather(feed_process(process, file_url), read_process(process))
            await process.wait()
            if process.returncode != 0:
                raise RuntimeError

        async with ChatActionSender.upload_voice(bot=message.bot, chat_id=message.chat.id):
            try:  # upload the slowed audio file to the user
                slowed_filename = await tg.get_filename_mention(message.bot, message.audio.file_name)
                input_audio_file = types.BufferedInputFile(processed_audio, filename=slowed_filename)
                upload_message = await tg.reply_audio(input_audio_file, message)
            except (TelegramAPIError, OSError, ValueError) as err:
                raise UploadError from err

    if upload_message.audio:  # save the match to the database
        new_match = MatchNew(
            original_id=message.audio.file_id,
            slowed_id=upload_message.audio.file_id,
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
