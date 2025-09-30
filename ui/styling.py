"""DataFrame styling utilities for the Streamlit UI."""

from typing import Dict, List

import pandas as pd

from domain.models import TrackRow
from logic.colors import duration_color


def create_playlist_dataframe(rows: List[TrackRow], time_target_mode: str = "Start Time", selected_song_index: int = None) -> pd.DataFrame:
    """Create a pandas DataFrame from TrackRow objects.

    Args:
        rows: List of TrackRow objects
        time_target_mode: "Start Time" or "End Time"
        selected_song_index: Index of selected song for end time targeting

    Returns:
        pd.DataFrame: DataFrame ready for display
    """
    data = []
    for i, row in enumerate(rows):
        row_data = {
            'Index': row.index,
            'Song name': row.name,
            'Artist': row.artists_display,
            'Song duration': row.duration_display,
            'Cumulative duration': row.cumulative_display,
            'Start time': row.approx_time_display,
            # Store raw values for styling (not displayed)
            '_duration_ms': row.duration_ms
        }
        
        # Add selection column for End Time mode
        if time_target_mode == "End Time":
            if selected_song_index == i:
                row_data['🎯 Target'] = "Selected"
            else:
                row_data['🎯 Target'] = f"Select"

        data.append(row_data)

    df = pd.DataFrame(data)

    # Set Index as the actual index
    df = df.set_index('Index')

    return df


def style_playlist_dataframe(df: pd.DataFrame, stats: Dict):
    """Apply color styling to the playlist DataFrame.

    Args:
        df: DataFrame created by create_playlist_dataframe
        stats: Statistics dict from load_playlist_rows

    Returns:
        pd.io.formats.style.Styler: Styled DataFrame ready for Streamlit display
    """
    def style_duration(col):
        # Get raw duration values from the dataframe
        raw_durations = df['_duration_ms']
        min_duration = stats.get('min_duration_ms', 0)
        max_duration = stats.get('max_duration_ms', 0)

        styles = []
        for duration_ms in raw_durations:
            color = duration_color(duration_ms, min_duration, max_duration)
            # Set black font color for better visibility
            styles.append(f'background-color: {color}; color: black')

        return styles

    # Build a view without helper columns for display
    visible_df = df.drop(columns=['_duration_ms'], errors='ignore')

    # Apply styling to duration column only
    styled = visible_df.style.apply(style_duration, subset=['Song duration'])

    return styled


def format_playlist_summary(stats: Dict) -> str:
    """Format playlist summary statistics for display.

    Args:
        stats: Statistics dict from load_playlist_rows

    Returns:
        str: Formatted summary string
    """
    total_tracks = stats.get('total_tracks', 0)
    total_duration_ms = stats.get('total_duration_ms', 0)

    # Format total duration
    from logic.formatting import ms_to_hhmmss
    total_duration_display = ms_to_hhmmss(total_duration_ms)

    summary = f"**{total_tracks} tracks** • **Total duration: {total_duration_display}**"

    return summary
