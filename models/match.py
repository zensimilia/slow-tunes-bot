from piccolo.columns import BigInt, Boolean, Serial, Varchar
from piccolo.table import Table

from .mixins import TimestampedMixin


class Match(Table, TimestampedMixin, tablename="matches"):
    pk = Serial(primary_key=True)
    original_id = Varchar(length=128, index=True)
    slowed_id = Varchar(length=128)
    is_private = Boolean(default=True)
    is_forbidden = Boolean(default=False)
    tg_user_id = BigInt(null=False)
