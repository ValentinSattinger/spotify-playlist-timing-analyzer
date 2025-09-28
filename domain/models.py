"""Domain models for Spotify playlist and track data."""

from typing import List, Optional

from pydantic import BaseModel, Field


class Artist(BaseModel):
    """Represents a Spotify artist."""
    name: str


class TrackRaw(BaseModel):
    """Raw track data from Spotify API."""
    id: str
    name: str
    artists: List[Artist]
    duration_ms: int




class TrackRow(BaseModel):
    """Processed track row ready for display in the table."""
    index: int = Field(..., description="1-based index in the playlist")
    name: str = Field(..., description="Track name")
    artists_display: str = Field(..., description="Comma-separated artist names")
    duration_ms: int = Field(..., description="Track duration in milliseconds")
    duration_display: str = Field(..., description="Formatted duration (MM:SS)")
    cumulative_ms: int = Field(..., description="Cumulative duration up to this track in milliseconds")
    cumulative_display: str = Field(..., description="Formatted cumulative duration (MM:SS)")
    approx_time_display: str = Field(..., description="Approximate play time (HH:MM) in selected timezone")
