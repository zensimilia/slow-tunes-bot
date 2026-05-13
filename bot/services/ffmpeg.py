import shlex
from enum import StrEnum, auto
from pathlib import Path
from typing import Self

MIN_BITRATE = 96
MAX_BITRATE = 320
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "fx"


class AnalogFX(StrEnum):
    VINYL = auto()
    TAPE = auto()
    HISS = auto()


class FFmpegCommandBuilder:
    def __init__(self, *, bitrate: int = 320, sample_rate: int = 48000) -> None:
        if not (MIN_BITRATE <= bitrate <= MAX_BITRATE):
            raise ValueError(f"Output bitrate should be in range {MIN_BITRATE}-{MAX_BITRATE}")
        self.bitrate = bitrate

        self.sample_rate = sample_rate
        self.args = ["-hide_banner", "-loglevel", "error", "-fflags", "+genpts"]
        self.effects = ["adelay=1000|1000"]
        self.master = []
        self.complex_in = []
        self.complex_out = []
        self._mix_num = 0
        self.input = ["-i", "pipe:0"]

    def __str__(self) -> str:
        """Return the shell-escaped command string."""
        return shlex.join(self.build())

    def speed(self, ratio: float) -> Self:
        speed_rate = int(self.sample_rate * ratio)
        self.effects.append(
            f"aresample={self.sample_rate},asetrate={speed_rate},aresample={self.sample_rate}",
        )
        return self

    def filters(
        self,
        *,
        lowpass_freq: int | None = None,
        highpass_freq: int | None = None,
        master: bool = False,
    ) -> Self:
        """
        Apply frequency-based filters.

        Args:
            lowpass_freq (optional): Cutoff frequency for the low-pass filter (Hz).
            highpass_freq (optional): Cutoff frequency for the high-pass filter (Hz).
        Returns:
            Self instance.
        """
        fx_list = self.master if master else self.effects
        if lowpass_freq is not None:
            fx_list.append(f"lowpass=f={lowpass_freq}")
        if highpass_freq is not None:
            fx_list.append(f"highpass=f={highpass_freq}")
        return self

    def reverb(self, intensity: float = 0.5) -> Self:
        inp, out = self._get_mix_names()
        self.complex_in.append(f"amovie={DATA_DIR / '220752.mp3'},aresample={self.sample_rate}[ir];")
        self.complex_out.append(f"[mix0]asplit=2[{inp}][split];")
        self.complex_out.append("[split][ir]afir=dry=1:wet=1:irnorm=0:irgain=0.5[reverb];")
        self.complex_out.append(
            f"[{inp}][reverb]amix=inputs=2:duration=first:normalize=0:weights='1 {intensity}'[{out}];"
        )
        return self

    def vibrato(self, *, freq: float = 1.5, depth: float = 0.2, master: bool = False) -> Self:
        fx_list = self.master if master else self.effects
        fx_list.append(f"vibrato=f={freq}:d={depth}")
        return self

    def _get_output_args(self) -> list[str]:
        return [
            *["-map", f"[mix{self._mix_num}]"],
            "-vn",
            *["-map_metadata", "0"],
            *["-disposition:v:0", "attached_pic"],
            *["-c:a", "libmp3lame"],
            *["-b:a", f"{self.bitrate}k"],
            *["-ar", str(self.sample_rate)],
            *["-ac", "2"],
            *["-write_xing", "0"],
            *["-id3v2_version", "3"],
            *["-write_id3v1", "1"],
            *["-f", "mp3", "pipe:1"],
        ]

    def _get_mix_names(self) -> tuple[str, str]:
        self._mix_num += 1
        return f"mix{self._mix_num - 1}", f"mix{self._mix_num}"

    def _mix(
        self,
        file_path: Path | str,
        *,
        name: str,
        loop: bool = False,
        weights: tuple[float, float] | None = None,
    ) -> None:
        loop_val = "0,asetpts=N/SR/TB" if loop else "1"
        weights_val = " ".join(str(w) for w in weights or (1, 1))
        self.complex_in.append(f"amovie={file_path}:loop={loop_val},aresample={self.sample_rate}[{name}];")
        inp, out = self._get_mix_names()
        self.complex_out.append(
            f"[{inp}][{name}]amix=inputs=2:duration=first:normalize=0:weights='{weights_val}'[{out}];"
        )

    def analog(self, fx: AnalogFX) -> Self:
        self._mix(DATA_DIR / f"{fx}.wav", name=fx.value, loop=True)
        return self

    def softclip(self, *, master: bool = False) -> Self:
        fx_list = self.master if master else self.effects
        fx_list.append("volume=2,asoftclip=type=tanh:threshold=0.8,alimiter")
        return self

    def build(self) -> list[str]:
        """Compile all components into a flat list of arguments for subprocess."""
        if self.master:
            inp, out = self._get_mix_names()
            self.complex_out.append(f"[{inp}]{','.join(self.master)}[{out}];")

        lavfi_filter = f"[0:a]{','.join(self.effects)}[mix0];"
        filter_complex = "".join([*self.complex_in, lavfi_filter, *self.complex_out])

        cmd = ["/usr/local/bin/ffmpeg", *self.args, *self.input]
        cmd += ["-lavfi", filter_complex]
        cmd += self._get_output_args()
        return cmd
