"""Playlist data processing and assembly pipeline."""

from datetime import datetime
from typing import Dict, List, Tuple, Optional

import pytz

from domain.models import TrackRaw, TrackRow, Artist
from logic.timing import compute_cumulative_ms, approx_times
from logic.formatting import ms_to_mmss, ms_to_hhmmss, dt_to_hhmm, join_artists
from spotify.client import SpotifyClient


def _extract_track_raw(track_data: Dict) -> TrackRaw:
    """Extract TrackRaw from Spotify API track response.

    Args:
        track_data: Raw track data from Spotify API

    Returns:
        TrackRaw: Parsed track data
    """
    track = track_data.get('track', track_data)  # Handle nested structure

    artists = [Artist(name=artist['name']) for artist in track.get('artists', [])]

    return TrackRaw(
        id=track['id'],
        name=track['name'],
        artists=artists,
        duration_ms=track['duration_ms']
    )


def _compute_playlist_stats(tracks: List[TrackRaw]) -> Dict:
    """Compute statistics needed for color scaling and display.

    Args:
        tracks: List of track data

    Returns:
        dict: Statistics including min/max values and totals
    """
    # Extract duration values
    duration_values = [track.duration_ms for track in tracks]

    # Compute stats
    stats = {
        'total_tracks': len(tracks),
        'total_duration_ms': sum(duration_values),
        'min_duration_ms': min(duration_values) if duration_values else 0,
        'max_duration_ms': max(duration_values) if duration_values else 0,
    }

    return stats


def load_playlist_rows(
    playlist_url: str,
    start_dt: datetime,
    tz: pytz.BaseTzInfo
) -> Tuple[List[TrackRow], Dict]:
    """Load and process playlist data into display-ready rows.

    Args:
        playlist_url: Spotify playlist URL, URI, or ID
        start_dt: Starting datetime for approximate time calculations
        tz: Timezone for approximate time calculations

    Returns:
        tuple: (list of TrackRow objects, stats dict)

    Raises:
        ValueError: If playlist parsing fails
        Exception: If Spotify API calls fail
    """
    # Step 1: Parse playlist ID
    client = SpotifyClient()
    playlist_id = client.parse_playlist_id(playlist_url)

    # Step 2: Fetch playlist metadata and tracks
    playlist_meta = client.get_playlist_meta(playlist_id)
    track_data_list = client.get_playlist_tracks(playlist_id)

    # Step 3: Extract TrackRaw objects
    tracks = [_extract_track_raw(track_data) for track_data in track_data_list]


    # Step 4: Compute cumulative durations
    durations_ms = [track.duration_ms for track in tracks]
    cumulative_ms_list = compute_cumulative_ms(durations_ms)

    # Step 5: Compute approximate times
    approx_dts = approx_times(start_dt, cumulative_ms_list, tz)

    # Step 6: Build TrackRow objects
    rows = []
    for i, (track, cumulative_ms, approx_dt) in enumerate(
        zip(tracks, cumulative_ms_list, approx_dts)
    ):
        # Format display strings
        artists_display = join_artists(track.artists)
        duration_display = ms_to_mmss(track.duration_ms)
        cumulative_display = ms_to_hhmmss(cumulative_ms)
        approx_time_display = dt_to_hhmm(approx_dt)

        row = TrackRow(
            index=i + 1,  # 1-based indexing
            name=track.name,
            artists_display=artists_display,
            duration_ms=track.duration_ms,
            duration_display=duration_display,
            cumulative_ms=cumulative_ms,
            cumulative_display=cumulative_display,
            approx_time_display=approx_time_display
        )
        rows.append(row)

    # Step 7: Compute table-level stats
    stats = _compute_playlist_stats(tracks)

    return rows, stats
