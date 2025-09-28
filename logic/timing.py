"""Timing calculation utilities for playlist duration and scheduling."""

from datetime import datetime, timedelta
from typing import List

import pytz


def compute_cumulative_ms(durations_ms: List[int]) -> List[int]:
    """Compute cumulative durations in milliseconds.

    Args:
        durations_ms: List of track durations in milliseconds

    Returns:
        list[int]: Cumulative durations where each element is the sum
                   of all durations up to and including that track
    """
    cumulative = []
    running_total = 0

    for duration in durations_ms:
        running_total += duration
        cumulative.append(running_total)

    return cumulative


def approx_times(start_dt: datetime, cumulative_ms: List[int], tz: pytz.BaseTzInfo) -> List[datetime]:
    """Calculate approximate play times for each track.

    Args:
        start_dt: Starting datetime
        cumulative_ms: Cumulative durations in milliseconds for each track
        tz: Timezone for the result datetimes

    Returns:
        list[datetime]: Approximate play times in the specified timezone,
                       handling day rollover correctly
    """
    times = []

    for cumulative in cumulative_ms:
        # Convert milliseconds to timedelta
        duration_delta = timedelta(milliseconds=cumulative)

        # Add duration to start time
        approx_dt = start_dt + duration_delta

        # Convert to specified timezone (this handles DST transitions automatically)
        if approx_dt.tzinfo is None:
            # If start_dt was naive, localize it first
            approx_dt = tz.localize(approx_dt)
        else:
            # If start_dt was aware, convert to target timezone
            approx_dt = approx_dt.astimezone(tz)

        times.append(approx_dt)

    return times
