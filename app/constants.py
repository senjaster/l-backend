"""Application-wide constants"""
from datetime import datetime, timezone

# Default timestamp for filtering - represents "beginning of time" for our application
# Used when no modified_since filter is provided to return all records
DEFAULT_MODIFIED_SINCE = datetime(1790, 1, 1, tzinfo=timezone.utc)