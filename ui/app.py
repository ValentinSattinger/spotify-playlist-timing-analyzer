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
def load_playlist_cached(playlist_url: str, start_dt: datetime, tz_name: str, crossover_seconds: int):
    """Cached version of playlist loading.

    Args:
        playlist_url: Spotify playlist URL/URI/ID
        start_dt: Start datetime for timing calculations
        tz_name: Timezone name
        crossover_seconds: Seconds lost at end of each song due to crossfade

    Returns:
        tuple: (rows, stats) from load_playlist_rows
    """
    tz = pytz.timezone(tz_name)
    return load_playlist_rows(playlist_url, start_dt, tz, crossover_seconds)


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

    # Start time inputs
    col1, col2 = st.sidebar.columns(2)

    with col1:
        start_time = st.time_input(
            "Start Time",
            value=datetime.strptime("20:30", "%H:%M").time(),
            help="When the playlist will start playing"
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

    # Main content area
    if analyze_button and playlist_url.strip():
        try:
            # Clear cache before loading new data
            load_playlist_cached.clear()
            
            with st.spinner("Loading playlist data..."):
                # Parse playlist ID for caching key
                client = SpotifyClient()
                playlist_id = client.parse_playlist_id(playlist_url.strip())

                # Load playlist data
                rows, stats = load_playlist_cached(playlist_url.strip(), start_dt, timezone_name, crossover_seconds)

            if not rows:
                st.error("No tracks found in this playlist.")
                return

            # Display summary
            st.header("📊 Playlist Summary")
            summary_text = format_playlist_summary(stats)
            st.markdown(summary_text)

            # Create and display the styled DataFrame
            st.header("🎼 Playlist Timeline")

            df = create_playlist_dataframe(rows)
            styled_df = style_playlist_dataframe(df, stats)

            # Display the table
            st.dataframe(styled_df)

            # Export functionality
            st.header("💾 Export Data")

            # CSV export
            csv_buffer = io.StringIO()
            # Convert styled dataframe back to regular dataframe for export
            df_for_export = df.drop(columns=['_bpm_raw', '_duration_ms'], errors='ignore')
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

    # Footer
    st.markdown("---")
    st.markdown(
        "Built with Streamlit, Spotipy, and Pandas. "
        "Make sure to configure your Spotify API credentials."
    )


if __name__ == "__main__":
    main()
