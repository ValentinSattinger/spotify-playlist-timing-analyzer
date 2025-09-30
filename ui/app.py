"""Streamlit application for Spotify Playlist Timing Analyzer."""

import io
import sys
import os
from datetime import datetime, date, timedelta
from pathlib import Path

import pytz
import streamlit as st

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from spotify.playlist import load_playlist_rows
from spotify.client import SpotifyClient
from ui.styling import create_playlist_dataframe, style_playlist_dataframe, format_playlist_summary


# Common timezones for the dropdown
COMMON_TIMEZONES = [
    "Europe/Helsinki",
    "US/Eastern",
    "US/Central",
    "US/Mountain",
    "US/Pacific",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Asia/Tokyo",
    "Australia/Sydney",
    "UTC"
]


def get_next_saturday():
    """Get the next upcoming Saturday date."""
    today = date.today()
    # Saturday is weekday 5 (Monday=0, Sunday=6)
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:  # If today is Saturday, get next Saturday
        days_until_saturday = 7
    return today + timedelta(days=days_until_saturday)


@st.cache_data
def load_playlist_cached(playlist_url: str, start_dt: datetime, tz_name: str, crossover_seconds: int, time_target_mode: str, selected_song_index: int = None):
    """Cached version of playlist loading.

    Args:
        playlist_url: Spotify playlist URL/URI/ID
        start_dt: Start datetime for timing calculations
        tz_name: Timezone name
        crossover_seconds: Seconds lost at end of each song due to crossfade
        time_target_mode: "Start Time" or "End Time"
        selected_song_index: Index of song to target for end time (0-based)

    Returns:
        tuple: (rows, stats) from load_playlist_rows
    """
    tz = pytz.timezone(tz_name)
    return load_playlist_rows(playlist_url, start_dt, tz, crossover_seconds, time_target_mode, selected_song_index)


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Spotify Playlist Analyzer",
        page_icon="🎵",
        layout="wide"
    )

    st.title("🎵 Spotify Playlist Timing Analyzer")
    st.markdown("Analyze your Spotify playlists with timing calculations and duration visualization.")

    # Sidebar inputs
    st.sidebar.header("Playlist Configuration")

    # Playlist URL input
    playlist_url = st.sidebar.text_input(
        "Spotify Playlist URL",
        value="https://open.spotify.com/playlist/6oQtOu9OmfQCL5teB03nC6?si=dfa5f9973eca421e",
        placeholder="https://open.spotify.com/playlist/... or spotify:playlist:...",
        help="Paste a Spotify playlist URL, URI, or ID"
    )

    # Time target mode setting
    time_target_mode = st.sidebar.radio(
        "Time Target Mode",
        options=["Start Time", "End Time"],
        index=0,
        help="Choose whether to target the start time or end time of the playlist"
    )

    # Initialize session state for song selection
    if 'selected_song_index' not in st.session_state:
        st.session_state.selected_song_index = None
    
    # Song selection for end time targeting
    if time_target_mode == "End Time":
        st.sidebar.markdown("**Select target song for end time:**")
        st.sidebar.markdown("*After analyzing, click a song to sync end time to that song*")

    # Start time inputs
    col1, col2 = st.sidebar.columns(2)

    with col1:
        time_label = "Start Time" if time_target_mode == "Start Time" else "End Time"
        time_help = "When the playlist will start playing" if time_target_mode == "Start Time" else "When the playlist should end"
        start_time = st.time_input(
            time_label,
            value=datetime.strptime("20:30", "%H:%M").time(),
            help=time_help
        )

    with col2:
        start_date = st.date_input(
            "Start Date (Optional)",
            value=get_next_saturday(),
            help="Date for the playlist start (defaults to next Saturday)"
        )

    # Timezone selection
    timezone_name = st.sidebar.selectbox(
        "Timezone",
        options=COMMON_TIMEZONES,
        index=COMMON_TIMEZONES.index("Europe/Helsinki") if "Europe/Helsinki" in COMMON_TIMEZONES else 0,
        help="Timezone for approximate time calculations"
    )

    # Crossover seconds setting
    crossover_seconds = st.sidebar.number_input(
        "Crossover Seconds",
        min_value=0,
        max_value=30,
        value=6,
        step=1,
        help="Seconds lost at the end of each song due to Spotify crossfade (default: 6s)"
    )

    # Combine date and time
    start_dt = datetime.combine(start_date, start_time)

    # Analysis button
    analyze_button = st.sidebar.button(
        "🎵 Analyze Playlist",
        type="primary",
        use_container_width=True
    )

    # Persist the last successful analysis inputs so selection-triggered reruns still render
    if 'analysis_context' not in st.session_state:
        st.session_state.analysis_context = None

    # Determine whether to analyze: either button pressed now, or we have prior context
    has_context = st.session_state.analysis_context is not None
    should_analyze = (analyze_button and playlist_url.strip()) or has_context

    if should_analyze:
        try:
            # If analyze was just pressed, set/refresh context from current controls
            if analyze_button and playlist_url.strip():
                st.session_state.analysis_context = {
                    'playlist_url': playlist_url.strip(),
                    'start_dt': start_dt,
                    'timezone_name': timezone_name,
                    'crossover_seconds': crossover_seconds,
                    'time_target_mode': time_target_mode,
                }
                # Clear cache before loading new data set
                load_playlist_cached.clear()

            # Resolve inputs from context
            ctx = st.session_state.analysis_context

            with st.spinner("Loading playlist data..."):
                # Parse playlist ID for caching key
                client = SpotifyClient()
                playlist_id = client.parse_playlist_id(ctx['playlist_url'])

                # Load playlist data
                rows, stats = load_playlist_cached(
                    ctx['playlist_url'],
                    ctx['start_dt'],
                    ctx['timezone_name'],
                    ctx['crossover_seconds'],
                    ctx['time_target_mode'],
                    st.session_state.selected_song_index
                )

            if not rows:
                st.error("No tracks found in this playlist.")
                return

            # Display summary
            st.header("📊 Playlist Summary")
            summary_text = format_playlist_summary(stats)
            st.markdown(summary_text)

            # Create and display the styled DataFrame
            st.header("🎼 Playlist Timeline")

            df = create_playlist_dataframe(rows, time_target_mode, st.session_state.selected_song_index)
            styled_df = style_playlist_dataframe(df, stats)

            # Display the table with trailing per-row Select buttons in End Time mode
            if time_target_mode == "End Time":
                # Show current selection status
                if st.session_state.selected_song_index is not None:
                    selected_row = rows[st.session_state.selected_song_index]
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.info(f"🎯 **Currently targeting:** {selected_row.name} - {selected_row.artists_display}")
                    with col2:
                        if st.button("Clear Selection", key="clear_selection"):
                            st.session_state.selected_song_index = None
                            load_playlist_cached.clear()
                            st.rerun()

                # Render a custom table with a trailing Select button column
                # Header
                header_cols = st.columns([1, 5, 4, 2, 3, 3, 2])
                header_cols[0].markdown("**#**")
                header_cols[1].markdown("**Song name**")
                header_cols[2].markdown("**Artist**")
                header_cols[3].markdown("**Song duration**")
                header_cols[4].markdown("**Cumulative duration**")
                header_cols[5].markdown("**Start time**")
                header_cols[6].markdown("**🎯 Target**")

                # Rows
                for i, row in enumerate(rows):
                    row_cols = st.columns([1, 5, 4, 2, 3, 3, 2])
                    row_cols[0].write(f"{row.index}")
                    row_cols[1].write(row.name)
                    row_cols[2].write(row.artists_display)
                    row_cols[3].write(row.duration_display)
                    row_cols[4].write(row.cumulative_display)
                    row_cols[5].write(row.approx_time_display)
                    if st.session_state.selected_song_index == i:
                        row_cols[6].button("Selected", key=f"selected_btn_{i}", disabled=True)
                    else:
                        if row_cols[6].button("Select", key=f"select_btn_{i}"):
                            st.session_state.selected_song_index = i
                            load_playlist_cached.clear()
                            st.rerun()
            else:
                # Display table with styling for Start Time mode
                st.dataframe(styled_df, use_container_width=True)


            # Export functionality
            st.header("💾 Export Data")

            # CSV export
            csv_buffer = io.StringIO()
            # Convert styled dataframe back to regular dataframe for export
            df_for_export = df.drop(columns=['_duration_ms'], errors='ignore')
            df_for_export.to_csv(csv_buffer, index=True)
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"playlist_analysis_{playlist_id}.csv",
                mime="text/csv",
                help="Download the playlist analysis as a CSV file"
            )

        except ValueError as e:
            st.error(f"Invalid playlist URL: {str(e)}")
        except Exception as e:
            st.error(f"Error loading playlist: {str(e)}")
            st.info("Make sure your Spotify credentials are configured correctly.")

    elif analyze_button:
        st.warning("Please enter a playlist URL.")



if __name__ == "__main__":
    main()
