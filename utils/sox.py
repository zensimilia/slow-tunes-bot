import asyncio
import io


class SoxException(Exception):
    """Base exception for sox-related errors."""


def get_sox_cli_args() -> list[str]:
    io = ["-t", "mp3", "-", "-t", "mp3", "-C", "320.2", "-"]  # Output to MP3 directly in sox
    # Reverberence, HF damping, Room scale, Stereo depth, Pre delay, Wet gain
    reverb = ["reverb", "70", "30", "100", "50"]
    bass = ["bass", "+3"]  # Gain bass in dB
    pad = ["pad", "0", "3"]  # Add 3 seconds of silence at the end of the track
    highpass = ["highpass", "50"]  # High-pass filter with a cutoff frequency of 50 Hz
    _gain = ["gain", "-3"]  # Reduce the overall gain by 3 dB to prevent clipping
    speed = ["speed", str(33 / 45)]  # Adjust the speed of the audio
    norm = ["norm", "-1"]  # Normalize the audio to -1 dB to prevent clipping after speed change

    return ["-q", *io, *speed, *highpass, *reverb, *bass, *pad, *norm]


async def proceed_audio(input_buffer: io.BytesIO) -> bytes:
    """This function slow down audio file and convert it to MP3 using sox."""

    input_buffer.seek(0)
    data = input_buffer.read()

    sox_process = await asyncio.create_subprocess_exec(
        "sox",
        *get_sox_cli_args(),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )

    sox_output, sox_err = await sox_process.communicate(data)

    if sox_err:
        raise SoxException(f"Sox error: {sox_err.decode()}")

    return sox_output
