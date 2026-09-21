from datetime import datetime, timezone

from sqlalchemy import DateTime, TypeDecorator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """Stores every timestamp as UTC and always hands one back with tzinfo attached.

    SQLite has no timezone-aware type and returns naive values, which the browser
    then interprets as local time. Normalising here means the API emits an explicit
    offset on SQLite and Postgres alike.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


TimestampColumn = UTCDateTime()
