"""String formatting utilities for display."""

from datetime import datetime
from typing import List

from domain.models import Artist


def ms_to_mmss(ms: int) -> str:
    """Convert milliseconds to MM:SS format.

    Args:
        ms: Duration in milliseconds

    Returns:
        str: Formatted duration as "MM:SS"

    Examples:
        >>> ms_to_mmss(213000)
        '03:33'
        >>> ms_to_mmss(60000)
        '01:00'
    """
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def ms_to_hhmmss(ms: int) -> str:
    """Convert milliseconds to HHh MMm SSs format.

    Args:
        ms: Duration in milliseconds

    Returns:
        str: Formatted duration as "HHh MMm SSs"

    Examples:
        >>> ms_to_hhmmss(3661000)
        '01h 01m 01s'
        >>> ms_to_hhmmss(7200000)
        '02h 00m 00s'
        >>> ms_to_hhmmss(125000)
        '00h 02m 05s'
    """
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"


def dt_to_hhmm(dt: datetime) -> str:
    """Convert datetime to HH:MM format (24-hour).

    Args:
        dt: Datetime object

    Returns:
        str: Time formatted as "HH:MM"

    Examples:
        >>> from datetime import datetime
        >>> dt_to_hhmm(datetime(2023, 1, 1, 14, 30))
        '14:30'
    """
    return dt.strftime("%H:%M")


def join_artists(artists: List[Artist]) -> str:
    """Join artist names with commas.

    Args:
        artists: List of Artist objects

    Returns:
        str: Comma-separated artist names

    Examples:
        >>> from domain.models import Artist
        >>> artists = [Artist(name="Artist 1"), Artist(name="Artist 2")]
        >>> join_artists(artists)
        'Artist 1, Artist 2'
    """
    return ", ".join(artist.name for artist in artists)
