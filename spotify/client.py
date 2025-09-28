"""Spotify API client wrapper with retry logic and utility methods."""

import re
from typing import Dict, List, Optional

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, retry_if_not_exception_type

from config.settings import get_settings


class SpotifyClient:
    """Spotify API client with automatic retries and error handling."""

    def __init__(self):
        """Initialize the Spotify client with credentials from settings."""
        settings = get_settings()
        credentials = SpotifyClientCredentials(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret
        )
        self.client = spotipy.Spotify(client_credentials_manager=credentials)

    @staticmethod
    def parse_playlist_id(url_or_id: str) -> str:
        """Parse a Spotify playlist URL, URI, or ID to extract the playlist ID.

        Args:
            url_or_id: Full URL, URI, or raw playlist ID

        Returns:
            str: The playlist ID

        Raises:
            ValueError: If the input format is not recognized
        """
        # Handle full URLs like https://open.spotify.com/playlist/<id>
        url_pattern = r'https?://open\.spotify\.com/playlist/([a-zA-Z0-9]+)'
        match = re.search(url_pattern, url_or_id)
        if match:
            return match.group(1)

        # Handle URIs like spotify:playlist:<id>
        uri_pattern = r'spotify:playlist:([a-zA-Z0-9]+)'
        match = re.search(uri_pattern, url_or_id)
        if match:
            return match.group(1)

        # Handle raw IDs (22 characters, alphanumeric)
        if re.match(r'^[a-zA-Z0-9]{22}$', url_or_id):
            return url_or_id

        raise ValueError(
            f"Invalid playlist identifier: {url_or_id}. "
            "Expected a Spotify playlist URL, URI, or 22-character ID."
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(spotipy.exceptions.SpotifyException)
    )
    def get_playlist_meta(self, playlist_id: str) -> Dict:
        """Get playlist metadata.

        Args:
            playlist_id: Spotify playlist ID

        Returns:
            dict: Playlist metadata
        """
        return self.client.playlist(playlist_id)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(spotipy.exceptions.SpotifyException)
    )
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """Get all tracks from a playlist, handling pagination.

        Args:
            playlist_id: Spotify playlist ID

        Returns:
            list[dict]: List of track objects
        """
        tracks = []
        results = self.client.playlist_tracks(playlist_id)

        while results:
            tracks.extend(results['items'])
            # Check if there are more pages
            if results['next']:
                results = self.client.next(results)
            else:
                break

        return tracks

    def _audio_features_batch(self, batch: List[str]) -> List[Optional[Dict]]:
        """Fetch audio features for a single batch of up to 100 track IDs.

        No retry logic here - we'll handle retries/errors at a higher level.
        """
        try:
            return self.client.audio_features(batch)
        except spotipy.exceptions.SpotifyException as e:
            # Re-raise 403 errors immediately (don't retry permission issues)
            if e.http_status == 403:
                raise e
            # For other errors, let the caller handle retries
            raise e

    def get_audio_features(self, track_ids: List[str]) -> Dict[str, Optional[Dict]]:
        """Get audio features for multiple tracks (batched requests of max 100).

        Args:
            track_ids: List of Spotify track IDs

        Returns:
            dict[str, dict]: Mapping of track_id to audio features dict, or None if not found
        """
        if not track_ids:
            return {}

        # Spotify API allows max 100 tracks per request
        batch_size = 100
        features_map: Dict[str, Optional[Dict]] = {}

        for i in range(0, len(track_ids), batch_size):
            batch = [tid for tid in track_ids[i:i + batch_size] if tid]
            if not batch:
                continue

            try:
                # Try once per batch - if it fails with 403, don't retry
                features_list = self._audio_features_batch(batch)
                for track_id, features in zip(batch, features_list):
                    features_map[track_id] = features
            except spotipy.exceptions.SpotifyException as e:
                if e.http_status == 403:
                    # Permission denied - mark all tracks in this batch as None
                    # and continue with other batches (they might work)
                    for track_id in batch:
                        features_map[track_id] = None
                else:
                    # For other errors, re-raise to let caller handle
                    raise e
            except Exception:
                # For non-Spotify exceptions, mark batch as None
                for track_id in batch:
                    features_map[track_id] = None

        return features_map
