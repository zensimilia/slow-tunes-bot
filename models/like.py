from piccolo.columns import BigInt, Serial
from piccolo.table import Table

from .mixins import TimestampedMixin


class Like(Table, TimestampedMixin, tablename="likes"):
    pk = Serial(primary_key=True)
    user_pk = BigInt()
    match_pk = BigInt()
