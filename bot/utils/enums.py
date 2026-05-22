from enum import StrEnum, auto


class Btn(StrEnum):
    BACK = auto()
    NONE = auto()


class FxAnalog(StrEnum):
    NONE = auto()
    VINYL = auto()
    TAPE = auto()
    HISS = auto()
