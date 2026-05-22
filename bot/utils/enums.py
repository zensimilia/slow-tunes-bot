from enum import StrEnum, auto


class Btn(StrEnum):
    BACK = auto()
    NONE = auto()


class FxAnalog(StrEnum):
    NONE = auto()
    VINYL = auto()
    TAPE = auto()
    HISS = auto()


class FxReverb(StrEnum):
    NONE = auto()
    NORMAL = auto()
    EXTREME = auto()
