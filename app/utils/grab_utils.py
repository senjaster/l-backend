"""Utility functions for plant grab management"""
from typing import Optional
from datetime import datetime, timezone, time, timedelta


def is_grab_expired(grabbed_at: Optional[datetime]) -> bool:
    """
    Check if grab has expired. Grab expires at 3:00 AM Moscow time (UTC+3) every day.
    
    Args:
        grabbed_at: The timestamp when the plant was grabbed
        
    Returns:
        True if grab has expired, False otherwise
    """
    if grabbed_at is None:
        return True
    
    # Get current time in UTC
    now_utc = datetime.now(timezone.utc)
    
    # Convert grabbed_at to UTC if it has timezone info, otherwise assume UTC
    if grabbed_at.tzinfo is None:
        grabbed_at = grabbed_at.replace(tzinfo=timezone.utc)
    
    # Calculate the most recent 3:00 AM Moscow time (00:00 AM UTC)
    # Moscow is UTC+3, so 3:00 AM Moscow = 00:00 UTC
    today_3am_moscow_utc = datetime.combine(now_utc.date(), time(0, 0), tzinfo=timezone.utc)
    
    # If current time is before today's 3:00 AM Moscow, use yesterday's 3:00 AM
    if now_utc < today_3am_moscow_utc:
        expiration_time = today_3am_moscow_utc
    else:
        # Current time is after today's 3:00 AM, so next expiration is tomorrow's 3:00 AM
        expiration_time = today_3am_moscow_utc + timedelta(days=1)
    
    # Find the last 3:00 AM that occurred after the grab
    last_3am = today_3am_moscow_utc
    if now_utc < today_3am_moscow_utc:
        last_3am = today_3am_moscow_utc - timedelta(days=1)
    
    # Grab is expired if the last 3:00 AM occurred after the grab time
    return grabbed_at < last_3am
