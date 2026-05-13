import shlex
from enum import StrEnum, auto
from pathlib import Path
from typing import Self

MIN_BITRATE = 96
MAX_BITRATE = 320
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "fx"


class FxAnalog(StrEnum):
    VINYL = auto()
    TAPE = auto()
    HISS = auto()

    @property
    def emoji(self) -> str:
        mapping = {
            FxAnalog.VINYL: "📀",
            FxAnalog.TAPE: "📽️",
            FxAnalog.HISS: "📼",
        }
        return mapping.get(self, "🔵")


class FFmpegCommandBuilder:
    def __init__(self, *, bitrate: int = 320, sample_rate: int = 48000, executable: str | None = None) -> None:
        if not (MIN_BITRATE <= bitrate <= MAX_BITRATE):
            raise ValueError(f"Output bitrate should be in range {MIN_BITRATE}-{MAX_BITRATE}")

        self.executable = self._escape_path(Path(executable or "/usr/local/bin/ffmpeg"))
        self.bitrate = bitrate
        self.sample_rate = sample_rate
        self.args = ["-hide_banner", "-loglevel", "error", "-fflags", "+genpts"]
        self.input = ["-i", "pipe:0"]

        self.input_effects = ["adelay=1000|1000"]
        self.mix_steps = []
        self.master_effects = []
        self.output_effects = ["alimiter"]

    def __str__(self) -> str:
        return shlex.join(self.build())

    def _escape_path(self, path: Path) -> str:
        return path.as_posix().replace(":", "\\:")

    def speed(self, ratio: float) -> Self:
        speed_rate = int(self.sample_rate * ratio)
        self.input_effects.append(f"asetrate={speed_rate},aresample={self.sample_rate}:dither_method=shibata")
        return self

    def filters(
        self,
        *,
        lowpass_freq: int | None = None,
        highpass_freq: int | None = None,
        master: bool = False,
    ) -> Self:
        fx_list = self.master_effects if master else self.input_effects
        if lowpass_freq is not None:
            fx_list.append(f"lowpass=f={lowpass_freq}")
        if highpass_freq is not None:
            fx_list.append(f"highpass=f={highpass_freq}")
        return self

    def flutter(
        self,
        *,
        freq: float = 1.5,
        depth: float = 0.2,
        master: bool = False,
        pulsator: bool = True,
    ) -> Self:
        fx_list = self.master_effects if master else self.input_effects
        fx_list.append(f"vibrato=f={freq}:d={depth}")
        if pulsator:
            phi = 1.61803398875  # golden ratio magic
            fx_list.append(f"apulsator=hz={freq / phi}:amount={depth / phi}")
        return self

    def softclip(self, *, master: bool = False) -> Self:
        fx_list = self.master_effects if master else self.input_effects
        fx_list.append("volume=1.1,asoftclip=type=tanh")
        return self

    def compressor(
        self,
        *,
        threshold: str = "-20dB",
        ratio: int = 5,
        attack: int = 5,
        release: int = 100,
        master: bool = False,
    ) -> Self:
        fx_list = self.master_effects if master else self.input_effects
        fx_list.append(f"acompressor=threshold={threshold}:ratio={ratio}:attack={attack}:release={release}")
        return self

    def bandpass(self, *, freq: float = 1500, width: float = 800, master: bool = False) -> Self:
        fx_list = self.master_effects if master else self.input_effects
        fx_list.append(f"bandpass=f={freq}:t=h:w={width}")
        return self

    def reverb(self, intensity: float = 0.5) -> Self:
        def step(inp: str, out: str, idx: int) -> tuple[str, str]:
            path = self._escape_path(DATA_DIR / "ir.wav")
            nodes = [
                f"amovie={path},aresample={self.sample_rate}[ir{idx}]",
                f"[{inp}]asplit=2[{inp}_src][split{idx}]",
                f"[split{idx}][ir{idx}]afir=dry=1:wet=1:irnorm=0:irgain=0.5[reverb{idx}]",
                f"[{inp}_src][reverb{idx}]amix=inputs=2:duration=first:normalize=0:weights='1 {intensity}'[{out}]",
            ]
            return ";".join(nodes), out

        self.mix_steps.append(step)
        return self

    def analog(self, fx: FxAnalog, *, weight: float = 1) -> Self:
        def step(inp: str, out: str, idx: int) -> tuple[str, str]:
            path = self._escape_path(DATA_DIR / f"{fx}.wav")
            loop_val = "0,asetpts=N/SR/TB"
            nodes = [
                f"amovie={path}:loop={loop_val},aresample={self.sample_rate}[fx{idx}]",
                f"[{inp}][fx{idx}]amix=inputs=2:duration=first:normalize=0:weights='1 {weight}'[{out}]",
            ]
            return ";".join(nodes), out

        self.mix_steps.append(step)
        return self

    def build(self) -> list[str]:
        complex_out = []

        current_label = "mix0"
        complex_out.append(f"[0:a]{','.join(self.input_effects)}[{current_label}]")

        for idx, step_func in enumerate(self.mix_steps):
            next_label = f"mix{idx + 1}"
            filter_str, current_label = step_func(current_label, next_label, idx)
            complex_out.append(filter_str)

        final_label = f"{current_label}_master"
        master_fx = ",".join(self.master_effects + self.output_effects)
        complex_out.append(f"[{current_label}]{master_fx}[{final_label}]")
        current_label = final_label

        output_args = [
            "-vn",
            *["-map_metadata", "-1"],
            *["-write_xing", "0"],
            *["-id3v2_version", "4"],
            *["-write_id3v1", "0"],
            *["-map", f"[{current_label}]"],
            *["-c:a", "libmp3lame"],
            *["-b:a", f"{self.bitrate}k"],
            *["-ar", str(self.sample_rate)],
            *["-ac", "2"],
            *["-f", "mp3", "pipe:1"],
        ]

        cmd = [self.executable, *self.args, *self.input]
        cmd += ["-lavfi", ";".join(complex_out)]
        cmd += output_args
        return cmd
