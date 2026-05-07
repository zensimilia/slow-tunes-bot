import re
import shlex
import subprocess
from functools import lru_cache
from typing import Self


@lru_cache(maxsize=1)
def get_sox_supported_formats() -> list[str]:
    """
    Retrieve a list of audio file formats supported by the SoX tool.

    Returns:
        A list of supported audio file formats by the SoX tool.
    Raises:
        ValueError: If result list is empty or any error due operation.
    """
    try:
        output = subprocess.check_output(
            ["/usr/bin/sox", "--help"],
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="ignore",
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as err:
        raise ValueError from err

    match = re.search(r"AUDIO FILE FORMATS:\s*(.*)", output, re.IGNORECASE)
    if not match:
        raise ValueError

    if result := [fmt.lower() for fmt in match.group(1).strip().split()]:
        return result
    raise ValueError


class SoxCommandBuilder:
    """
    A fluent interface for building SoX (Sound eXchange) command-line arguments.

    This builder simplifies the construction of complex SoX pipelines, handling
    parameter ordering, formatting (percentages, decibels), and shell-safe
    string serialization.

    Attributes:
        args: Base SoX flags (verbosity, quiet mode, etc.).
        effects: Accumulated list of audio effects and their parameters.
        io: Input/output specifications including formats and piping.
    """

    def __init__(self, *, input_format: str, output_quality: str, supported_formats: list[str] | None = None) -> None:
        """
        Initialize the builder with stream formats.

        Args:
            input_format: Format of the input stream (e.g., 'wav', 'flac', 'mp3').
            output_quality: Compression factor for MP3 output (SoX -C flag).
            supported_formats (optional): List of supported formats.
        """
        self.format = input_format
        self.supported_formats = supported_formats or get_sox_supported_formats()

        self.args = ["-V1", "--multi-threaded"]
        self.effects = []
        self.io = ["-t", input_format, "-", "-t", "mp3", "-C", output_quality, "-"]

    def __str__(self) -> str:
        """Return the shell-escaped command string."""
        return self.build_string()

    def get_format(self) -> str:
        """Return the format attribute."""
        return self.format

    def get_suported_formats(self) -> list[str]:
        """Return a list of supported formats."""
        return self.supported_formats

    def is_format_supported(self, fmt: str) -> bool:
        """
        Check if a given format is supported by.

        Args:
            fmt: A format that you want to check.

        Returns:
            A boolean value.
        """
        return fmt.lower().removeprefix(".") in self.supported_formats

    def speed(self, ratio: float) -> Self:
        """
        Adjust the playback speed (affects both pitch and tempo).

        Args:
            ratio: Speed multiplier (e.g., 2.0 to double speed, 0.5 to halve it).
        Returns:
            Self instance.
        """
        self.effects.extend(["speed", str(ratio)])
        return self

    def reverb(  # noqa: PLR0913
        self,
        *,
        reverberance: int = 50,
        hf_damping: int = 50,
        scale: int = 100,
        stereo_depth: int = 100,
        pre_delay: int = 0,
        wet_gain: float = 0,
        wet_only: bool = False,
    ) -> Self:
        """
        Add a reverberation effect.

        Args:
            reverberance (optional): Percentage of "wet" essence [0-100].
                Defaults to 50.
            hf_damping (optional): High-frequency damping percentage [0-100].
                Defaults to 50.
            scale (optional): Room size percentage [0-100].
                Defaults to 100.
            stereo_depth(optional): Stereo width percentage [0-100].
                Defaults to 100.
            pre_delay (optional): Delay before the reverb starts in milliseconds.
                Defaults to 0.
            wet_gain (optional): Volume adjustment for the processed signal in dB.
                Defaults to 0.
            wet_only (optional): If True, output only the reverb artifacts without the dry signal.
                Defaults to False.
        Returns:
            Self instance.
        """
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
        """
        Boost or cut the bass frequencies using a shelving filter.

        Args:
            gain_db: Gain in decibels.
        Returns:
            Self instance.
        """
        self.effects.extend(["bass", self._db(gain_db)])
        return self

    def filters(self, *, lowpass_freq: int | None = None, highpass_freq: int | None = None) -> Self:
        """
        Apply frequency-based filters.

        Args:
            lowpass_freq (optional): Cutoff frequency for the low-pass filter (Hz).
            highpass_freq (optional): Cutoff frequency for the high-pass filter (Hz).
        Returns:
            Self instance.
        """
        if lowpass_freq is not None:
            self.effects.extend(["lowpass", self._freq(lowpass_freq)])
        if highpass_freq is not None:
            self.effects.extend(["highpass", self._freq(highpass_freq)])
        return self

    def gain(self, db: float) -> Self:
        """
        Adjust the overall volume of the signal.

        Args:
            db: Gain adjustment in decibels.
        Returns:
            Self instance.
        """
        self.effects.extend(["gain", self._db(db)])
        return self

    def normalize(self, db: float = -1) -> Self:
        """
        Normalize the audio to a specific peak level.

        Args:
            db (optional): Target peak level in decibels.
                Defaults to -1.
        Returns:
            Self instance.
        """
        self.effects.extend(["norm", self._db(db)])
        return self

    def padding(self, start: int, end: int) -> Self:
        """
        Add silence to the beginning and/or end of the audio.

        Args:
            start: Duration of silence at the start (seconds).
            end: Duration of silence at the end (seconds).
        Returns:
            Self instance.
        """
        self.effects.extend(["pad", str(start), str(end)])
        return self

    def dither(self) -> Self:
        """
        Add the "dither" effect to a list of effects.

        Returns:
            Self instance.
        """
        self.effects.extend(["dither"])
        return self

    def build_list(self) -> list[str]:
        """
        Compile all components into a flat list of arguments for subprocess.

        Returns:
            List of arguments.
        """
        return ["sox", *self.args, *self.io, *self.effects]

    def build_string(self) -> str:
        """
        Compile the command into a shell-ready string with proper escaping.

        Returns:
            Shell-ready string with arguments for subprocess.
        """
        return shlex.join(self.build_list())

    @classmethod
    def _db(cls, value: float) -> str:
        """Format a float as a signed dB string (e.g., '+3.0' or '-6.0')."""
        return f"{value:+}"

    @classmethod
    def _percent(cls, value: int) -> str:
        """Clamp a value between 0 and 100 and return as string."""
        return str(max(0, min(value, 100)))

    @classmethod
    def _freq(cls, value: int) -> str:
        """Ensure frequency is non-negative and return as string."""
        return str(max(0, value))
