import asyncio
import io

SOX_FMT = ["aif", "aifc", "aiff", "aiffc", "flac", "mp2", "mp3", "ogg", "opus", "vorbis"]
OUTPUT_MP3_QUALITY = "-0.9"


class SoxException(Exception):
    """Base exception for sox-related errors."""


def get_sox_cli_args(in_fmt: str = "mp3") -> list[str]:
    io = ["-t", in_fmt, "-", "-t", "mp3", "-C", OUTPUT_MP3_QUALITY, "-"]  # Output to MP3 directly in sox
    bass = ["bass", "+3"]  # Gain bass in dB
    pad = ["pad", "0", "2"]  # Add silence at the end of the track
    highpass = ["highpass", "50"]  # High-pass filter
    gain = ["gain", "-1"]  # Reduce the overall gain to prevent clipping
    speed = ["speed", str(33 / 45)]  # Adjust the speed of the audio
    norm = ["norm", "-1"]  # Normalize the audio

    # Reverberence, HF damping, Room scale, Stereo depth, Pre delay, Wet gain
    reverb = ["reverb", "70", "30", "100", "50"]

    return ["-V1", *io, *speed, *gain, *highpass, *reverb, *bass, *pad, *norm]


async def proceed_audio(input_buffer: io.BytesIO, fmt: str = "mp3") -> bytes:
    """This function slow down audio file and convert it to MP3 using sox."""

    sox_process = await asyncio.create_subprocess_exec(
        "sox",
        *get_sox_cli_args(fmt),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    input_buffer.seek(0)
    sox_output, sox_err = await sox_process.communicate(input_buffer.read())
    input_buffer.close()
    del input_buffer

    if sox_err:
        raise SoxException(f"Sox error: {sox_err.decode()}")

    return sox_output
