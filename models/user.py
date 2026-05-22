from piccolo.columns import JSON, BigInt, Serial, Varchar
from piccolo.table import Table
from pydantic import BaseModel

from bot.utils.enums import FxAnalog, FxReverb

from .mixins import TimestampedMixin

DEFAULT_USERNAME = "Private Person"


class UserOptions(BaseModel):
    fx_analog: FxAnalog = FxAnalog.NONE
    fx_reverb: FxReverb = FxReverb.NONE


class User(Table, TimestampedMixin, tablename="users"):
    pk = Serial(primary_key=True)
    tg_id = BigInt(unique=True)
    username = Varchar(default=DEFAULT_USERNAME, length=100)
    options = JSON(default=lambda: UserOptions().model_dump_json())

    def get_options(self) -> UserOptions:
        return UserOptions.model_validate_json(self.options)
