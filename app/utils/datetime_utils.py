"""Datetime utility functions"""

from datetime import datetime


def truncate_to_milliseconds(dt: datetime) -> datetime:
    """
    Truncate datetime to milliseconds (3 digits after decimal point).

    This is used for comparing timestamps with client-side timestamps that only
    store millisecond precision, preventing false positive concurrent modification errors.

    Args:
        dt: Datetime to truncate

    Returns:
        Datetime with microseconds truncated to milliseconds
    """
    return dt.replace(microsecond=(dt.microsecond // 1000) * 1000)
