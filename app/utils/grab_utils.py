"""Utility functions for plant claim management"""

from typing import Optional
from datetime import datetime, timezone, time, timedelta


def is_claim_expired(claimed_at: Optional[datetime]) -> bool:
    """
    Check if claim has expired. Claim expires at 3:00 AM Moscow time (UTC+3) every day.

    Args:
        claimed_at: The timestamp when the plant was claimed

    Returns:
        True if claim has expired, False otherwise
    """
    if claimed_at is None:
        return True

    # Get current time in UTC
    now_utc = datetime.now(timezone.utc)

    # Convert claimed_at to UTC if it has timezone info, otherwise assume UTC
    if claimed_at.tzinfo is None:
        claimed_at = claimed_at.replace(tzinfo=timezone.utc)

    # Calculate the most recent 3:00 AM Moscow time (00:00 AM UTC)
    # Moscow is UTC+3, so 3:00 AM Moscow = 00:00 UTC
    today_3am_moscow_utc = datetime.combine(
        now_utc.date(), time(0, 0), tzinfo=timezone.utc
    )

    # If current time is before today's 3:00 AM Moscow, use yesterday's 3:00 AM
    if now_utc < today_3am_moscow_utc:
        expiration_time = today_3am_moscow_utc
    else:
        # Current time is after today's 3:00 AM, so next expiration is tomorrow's 3:00 AM
        expiration_time = today_3am_moscow_utc + timedelta(days=1)

    # Find the last 3:00 AM that occurred after the claim
    last_3am = today_3am_moscow_utc
    if now_utc < today_3am_moscow_utc:
        last_3am = today_3am_moscow_utc - timedelta(days=1)

    # Claim is expired if the last 3:00 AM occurred after the claim time
    return claimed_at < last_3am
