import asyncio
import shlex
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    import io

SUPPORTED_FMT = ["aif", "aifc", "aiff", "aiffc", "flac", "mp2", "mp3", "ogg", "opus", "vorbis"]


class SoxError(Exception):
    """Base exception for sox-related errors."""

    def __init__(self, msg: str) -> None:
        super().__init__(f"Sox error: {msg}")


def is_supported_format(fmt: str) -> bool:
    return fmt in (SUPPORTED_FMT)


async def proceed_audio(input_buffer: io.BytesIO, sox_command: list[str]) -> bytes:
    """
    This Python async function processes audio data using SoX command and returns the output.

    :param input_buffer: `input_buffer` is a BytesIO object that contains audio data
    :type input_buffer: io.BytesIO
    :param sox_command: A list of strings representing the SoX command and its arguments that will be executed
    :type sox_command: list[str]
    :return: the output of processing the input audio data as bytes.
    """

    subprocess = await asyncio.create_subprocess_exec(
        *sox_command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    input_buffer.seek(0)
    result, error = await subprocess.communicate(input_buffer.read())

    if error:
        raise SoxError(error.decode())

    return result


class SoxCommandBuilder:
    def __init__(self, *, input_format: str, output_quality: str) -> None:
        self.args = ["sox", "-V1", "-q"]
        self.effects = []
        self.io = ["-t", input_format, "-", "-t", "mp3", "-C", output_quality, "-"]

    def __str__(self) -> str:
        return self.build_string()

    def speed(self, ratio: float) -> Self:
        self.effects.extend(["speed", str(ratio)])
        return self

    def reverb(  # noqa: PLR0913
        self,
        *,
        reverberance: int = 50,  # %
        hf_damping: int = 50,  # %
        scale: int = 100,  # %
        stereo_depth: int = 100,  # %
        pre_delay: int = 0,  # ms
        wet_gain: float = 0,  # db
        wet_only: bool = False,
    ) -> Self:
        self.effects.extend([
            "reverb",
            *(["-w"] if wet_only else []),
            self._percent(reverberance),
            self._percent(hf_damping),
            self._percent(scale),
            self._percent(stereo_depth),
            str(pre_delay),
            self._db(wet_gain),
        ])
        return self

    def bass(self, gain_db: float) -> Self:
        self.effects.extend(["bass", self._db(gain_db)])
        return self

    def filters(self, *, lowpass_freq: int | None = None, highpass_freq: int | None = None) -> Self:
        if lowpass_freq is not None:
            self.effects.extend(["lowpass", self._freq(lowpass_freq)])
        if highpass_freq is not None:
            self.effects.extend(["highpass", self._freq(highpass_freq)])
        return self

    def gain(self, db: float) -> Self:
        self.effects.extend(["gain", self._db(db)])
        return self

    def normalize(self, db: float = -1) -> Self:
        self.effects.extend(["norm", self._db(db)])
        return self

    def padding(self, start: int, end: int) -> Self:
        self.effects.extend(["pad", str(start), str(end)])
        return self

    def build_list(self) -> list[str]:
        return [*self.args, *self.io, *self.effects]

    def build_string(self) -> str:
        return shlex.join(self.build_list())

    @classmethod
    def _db(cls, value: float) -> str:
        return f"{value:+}"

    @classmethod
    def _percent(cls, value: int) -> str:
        return str(max(0, min(value, 100)))

    @classmethod
    def _freq(cls, value: int) -> str:
        return str(max(0, value))
