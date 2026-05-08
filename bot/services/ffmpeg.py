import shlex
from typing import Self


class FFmpegCommandBuilder:
    def __init__(self, *, bitrate: int = 320, sample_rate: int = 48000) -> None:
        self.sample_rate = sample_rate
        self.args = ["-hide_banner", "-loglevel", "warning", "-fflags", "+genpts"]
        self.effects = []
        self.input = ["-i", "pipe:0"]
        self.output = [
            "-vn",
            *["-map_metadata", "0"],
            *["-disposition:v:0", "attached_pic"],
            *["-c:a", "libmp3lame"],
            *["-b:a", f"{max(bitrate, 128)}k"],
            *["-ar", str(self.sample_rate)],
            *["-ac", "2"],
            *["-write_xing", "0"],
            *["-id3v2_version", "3"],
            *["-write_id3v1", "1"],
            *["-f", "mp3", "pipe:1"],
        ]

    def __str__(self) -> str:
        """Return the shell-escaped command string."""
        return shlex.join(self.build())

    def speed(self, ratio: float) -> Self:
        speed_rate = int(self.sample_rate * ratio)
        self.effects.append(
            f"volume=-1dB,aresample={self.sample_rate},asetrate={speed_rate},aresample={self.sample_rate}",
        )
        return self

    def reverb(self, *, intensity: float = 0.5, extrastereo: bool = True) -> Self:
        decay1 = 0.3 * intensity
        decay2 = 0.2 * intensity
        chain = f"aecho=0.6:0.7:40|60|91|133:0.4|{decay1}|{decay2}|0.1" + (",extrastereo=m=2.5" if extrastereo else "")
        self.effects.append(chain)
        return self

    def build(self) -> list[str]:
        """Compile all components into a flat list of arguments for subprocess."""
        cmd = ["/usr/local/bin/ffmpeg", *self.args, *self.input]
        if self.effects:
            cmd += ["-af", ",".join(self.effects) + ",asoftclip,volume=1.5,alimiter"]
        cmd += self.output
        return cmd
