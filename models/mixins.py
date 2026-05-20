from datetime import UTC, datetime

from piccolo.columns import Timestamptz


class TimestampedMixin:
    created_at = Timestamptz(default=datetime.now(UTC))
    updated_at = Timestamptz(auto_update=datetime.now(UTC))
