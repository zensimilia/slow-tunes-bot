import json
from dataclasses import asdict, dataclass

from piccolo.columns import JSON, BigInt, Serial, Varchar
from piccolo.table import Table

from .mixins import TimestampedMixin

DEFAULT_USERNAME = "Private Person"


@dataclass
class UserOptions:
    fx_analog: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


class User(Table, TimestampedMixin, tablename="users"):
    pk = Serial(primary_key=True)
    tg_id = BigInt(unique=True)
    username = Varchar(default=DEFAULT_USERNAME, length=100)
    options = JSON(default=lambda: UserOptions().as_dict())

    def get_options(self) -> UserOptions:
        data = self.options
        if isinstance(data, str):
            data = json.loads(data)
        return UserOptions(**data)
