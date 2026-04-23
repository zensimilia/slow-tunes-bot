import asyncio
import io
import os
from pathlib import Path

from aiogram import F, Router, flags, types

from core.config import config
from core.exceptions import DownloadError, FileIsTooBig, NoAudio
from core.messages import QUEUE_POSITION_TEXT
from core.queue import TaskQueue
from db.base import Database

audio_router = Router()

AUDIO_SIZE_LIMIT = 20 * 1024 * 1024  # 20 MB
CHUNK_SIZE = 64 * 1024  # 64 KB


@audio_router.message(F.audio)
@flags.rate_limit(rate=3, key="audio")
async def audio_handler(message: types.Message, db: Database, queue: TaskQueue) -> None:
    audio = message.audio
    if not audio or not audio.file_size:
        raise NoAudio("No audio file found in the message")

    audio_size = audio.file_size
    if audio_size >= AUDIO_SIZE_LIMIT:
        raise FileIsTooBig(f"Audio file is too big: {audio_size} bytes")

    task = queue.enqueue(slowing_down_task, message)

    if task > 1:
        await message.reply(QUEUE_POSITION_TEXT.format(task=task), disable_notification=True)


async def slowing_down_task(message: types.Message) -> None:
    assert message.bot
    assert message.audio

    input_buffer = io.BytesIO()

    try:
        await message.bot.download(file=message.audio, destination=input_buffer, seek=True, chunk_size=CHUNK_SIZE)
        input_buffer.seek(0)
        file_name = config.DATA_DIR / "downloads" / f"{message.audio.file_id}.mp3"
        await slow_down(file_name, input_buffer, message)
    except Exception as err:
        raise DownloadError(f"Failed to download audio file: {err}")


async def slow_down(file_path: str | Path, input_buffer: io.BytesIO, message: types.Message) -> str:
    """This function slow down audio file."""

    if isinstance(file_path, str):
        file_path = Path(file_path)

    mp3_file_path = file_path.with_name(f"{file_path.stem}_slow").with_suffix(".mp3")

    try:
        input_buffer.seek(0)
        input_data = input_buffer.read()

        # Reverberence, HF damping, Room scale, Stereo depth, Pre delay, Wet gain
        reverb = ["reverb", "70", "30", "100", "50"]
        bass = ["bass", "+3"]  # Gain in dB
        pad = ["pad", "0", "3"]  # Add 3 seconds of silence at the end of the track
        highpass = ["highpass", "50"]  # High-pass filter with a cutoff frequency of 50 Hz
        gain = ["gain", "-3"]  # Reduce the overall gain by 3 dB to prevent clipping
        speed = ["speed", str(33 / 45)]  # Adjust the speed of the audio
        sox_io = ["-t", "mp3", "-", "-t", "wav", "-"]
        sox_cmd = [
            "sox",
            "-q",  # quiet mode, suppresses all non-error messages
            *sox_io,
            *speed,
            *gain,
            *highpass,
            *reverb,
            *bass,
            *pad,
        ]
        ffmpeg_in = [
            "-i",
            "-",
        ]
        ffmpeg_cmd = [
            "ffmpeg",
            *["-hide_banner", "-loglevel", "error"],  # Suppress all output except errors
            "-y",
            *ffmpeg_in,
            "-c:a",
            "libmp3lame",
            "-q:a",
            "0",
            "-f",
            "mp3",
            "-",
        ]

        r, w = os.pipe()
        sox = await asyncio.create_subprocess_exec(
            *sox_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=w,
            stderr=asyncio.subprocess.DEVNULL,
        )
        ffmpeg = await asyncio.create_subprocess_exec(
            *ffmpeg_cmd,
            stdin=r,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        os.close(r)
        os.close(w)

        async def feed_sox(stdin, data):
            stdin.write(data)
            await stdin.drain()
            stdin.write_eof()

        (final_mp3_data, ffmpeg_err), _ = await asyncio.gather(ffmpeg.communicate(), feed_sox(sox.stdin, input_data))

        await sox.wait()

        if ffmpeg.returncode == 0:
            from aiogram.types import BufferedInputFile

            audio_file = BufferedInputFile(final_mp3_data, filename=f"{file_path.stem}_slow.mp3")
            await message.answer_audio(audio=audio_file, title=f"{file_path.stem} (slowed)", performer="AudioBot")
        else:
            error_msg = ffmpeg_err.decode() if ffmpeg_err else "Unknown error"
            print(f"FFmpeg error: {error_msg}")

    except Exception as error:
        raise Exception(f"Error processing audio file: {error}") from error

    return mp3_file_path.as_posix()
