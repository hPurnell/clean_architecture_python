from datetime import datetime, timezone


def utc_now() -> datetime:
    """The current time in UTC, naive, as the DateTime columns store it."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
