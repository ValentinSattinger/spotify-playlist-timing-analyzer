## Spotify Playlist Timing & BPM Analyzer — Implementation Plan

This plan defines an atomic, sequential set of steps that independent agents can implement one-by-one to build a lightweight local tool. The tool ingests a public Spotify playlist URL, fetches tracks and audio features (BPM), computes cumulative timing, and renders a sortable, color-scaled table with an adjustable start time to estimate when each song will play.

### Tech Stack

- **Language**: Python 3.10+
- **Runtime**: Local only
- **Libraries**: Streamlit (UI), Spotipy (Spotify Web API), Pandas (data), Python-dotenv (config), Pydantic (types/validation), Tenacity (retry), (optional) tzlocal/pytz (time zones)
- **Auth**: Spotify Client Credentials Flow (public playlist + audio features)

### High-Level Architecture

- `config/` — environment/config loading
- `spotify/` — Spotify API client wrappers and playlist ingestion
- `domain/` — typed models and validation
- `logic/` — computation of durations, cumulative times, color scales
- `ui/` — Streamlit app (single entrypoint)
- `data/` — local cache (optional)

---

## Step 0 — Repository Bootstrap

**Goal**: Initialize the project with environment, dependencies, and basic structure.

- Files/Dirs:

  - `.gitignore`
  - `README.md` (sparse, optional for now)
  - `requirements.txt`
  - `.env.example`
  - `config/__init__.py`, `config/settings.py`
  - `spotify/__init__.py`, `spotify/client.py`, `spotify/playlist.py`
  - `domain/__init__.py`, `domain/models.py`
  - `logic/__init__.py`, `logic/timing.py`, `logic/colors.py`, `logic/formatting.py`
  - `ui/app.py`

- Requirements (initial):

  - `streamlit`
  - `spotipy`
  - `pandas`
  - `python-dotenv`
  - `pydantic`
  - `tenacity`
  - `tzlocal` (optional)
  - `pytz` (optional)

- `.env.example` keys:

  - `SPOTIFY_CLIENT_ID=""`
  - `SPOTIFY_CLIENT_SECRET=""`

- Acceptance Criteria:
  - Project structure exists with empty modules
  - `pip install -r requirements.txt` succeeds
  - `.env.example` present with required keys

---

## Step 1 — Configuration Loader

**Goal**: Centralize environment loading and validation.

- Implement `config/settings.py`:

  - Load `.env` via `dotenv.load_dotenv()`
  - Define `Settings` pydantic model: `spotify_client_id`, `spotify_client_secret`, `default_timezone` (optional)
  - Provide `get_settings()` memoized accessor

- Acceptance Criteria:
  - Importing `get_settings()` returns validated, non-empty client credentials or raises a clear error message
  - Works when `.env` is present; provides meaningful error if missing keys

---

## Step 2 — Spotify Client Wrapper

**Goal**: Provide a thin, reliable wrapper over Spotipy using Client Credentials Flow.

- Implement `spotify/client.py`:

  - Build Spotipy client with `SpotifyClientCredentials`
  - Add tenacity `@retry` for transient errors (HTTP 429, 5xx)
  - Utility methods:
    - `parse_playlist_id(url_or_id: str) -> str` (accepts full URL, URI, or raw ID)
    - `get_playlist_meta(playlist_id: str) -> dict`
    - `get_playlist_tracks(playlist_id: str) -> list[dict]` (paginate until full)
    - `get_audio_features(track_ids: list[str]) -> dict[str, dict]` (batch requests of up to 100; return mapping id->features)

- Acceptance Criteria:
  - Given a known public playlist URL, returns all tracks (name, artists, id, duration_ms)
  - Given track IDs, returns audio features including `tempo` (BPM) where available
  - Gracefully handles missing IDs or missing features

---

## Step 3 — Domain Models

**Goal**: Define strong types for playlist and track rows.

- Implement `domain/models.py` with pydantic models:

  - `Artist(name: str)`
  - `TrackRaw(id: str, name: str, artists: list[Artist], duration_ms: int)`
  - `TrackFeatures(id: str, tempo: float | None)`
  - `TrackRow(index: int, name: str, artists_display: str, bpm: float | None, duration_ms: int, duration_display: str, cumulative_ms: int, cumulative_display: str, approx_time_display: str)`

- Acceptance Criteria:
  - Parsing raw Spotify responses into `TrackRaw` instances works
  - `TrackRow` represents a ready-to-render, fully computed row

---

## Step 4 — Timing & Formatting Utilities

**Goal**: Compute cumulative durations and approximate times; standardize display formatting.

- Implement `logic/timing.py`:

  - `compute_cumulative_ms(durations_ms: list[int]) -> list[int]`
  - `approx_times(start_dt: datetime, cumulative_ms: list[int], tz: tzinfo) -> list[datetime]`
  - Handle day rollover (times past midnight)

- Implement `logic/formatting.py`:

  - `ms_to_mmss(ms: int) -> str` (e.g., 213000 -> "03:33")
  - `dt_to_hhmm(dt: datetime) -> str` (e.g., 20:30)
  - `join_artists(artists: list[Artist]) -> str` (comma-separated)

- Acceptance Criteria:
  - Cumulative sums correct
  - Approximate times correct for arbitrary start times; rollover supported
  - Formatting helpers return expected strings

---

## Step 5 — Color Scale Utilities

**Goal**: Compute per-cell background colors for BPM and duration columns.

- Implement `logic/colors.py`:

  - Linear gradient function from green → yellow → red for a numeric range
  - `bpm_color(bpm: float | None, min_bpm: float, max_bpm: float) -> str` returning hex color
  - `duration_color(ms: int, min_ms: int, max_ms: int) -> str` returning hex color
  - Null-safe: return neutral background for `None`
  - Defaults: if all BPM equal or missing, use neutral colors

- Acceptance Criteria:
  - Deterministic color mapping across columns
  - Returns CSS-compatible color strings (e.g., `#e74c3c`)

---

## Step 6 — Playlist Assembly Pipeline

**Goal**: Convert raw Spotify data into the final `TrackRow` table.

- Implement in `spotify/playlist.py`:

  - `load_playlist_rows(playlist_url: str, start_dt: datetime, tz: tzinfo) -> tuple[list[TrackRow], dict]`
    - Steps:
      1. Parse playlist ID
      2. Fetch playlist metadata and tracks
      3. Extract `TrackRaw[]`
      4. Fetch audio features for all track IDs, map to BPM
      5. Compute cumulative_ms from durations
      6. Compute approx datetime per row
      7. Build `TrackRow[]` including formatted durations and approx times
      8. Compute table-level stats (e.g., min/max BPM, min/max duration, total duration)
    - Return `(rows, stats)` where `stats` includes ranges for color scales and `total_duration_ms`

- Acceptance Criteria:
  - For a given playlist URL and start time, returns fully populated rows with correct cumulative and approx times
  - Handles tracks missing BPM gracefully

---

## Step 7 — DataFrame Styling Adapters

**Goal**: Bind color utilities to a Pandas Styler that Streamlit can render.

- In `ui/app.py` or a small helper module:

  - Build a `pandas.DataFrame` from `TrackRow[]`
  - Provide a `style_dataframe(df, stats)` function that applies per-cell background colors for `BPM` and `Song duration`
    - Use `df.style.apply` with functions that return CSS styles per column

- Acceptance Criteria:
  - A DataFrame Styler object exists with BPM and Duration columns color-coded
  - Neutral color applied where values are missing

---

## Step 8 — Streamlit UI

**Goal**: Provide a simple UI to input playlist URL and start time, trigger analysis, and view results.

- Implement `ui/app.py`:

  - Sidebar inputs:
    - Playlist URL (text input)
    - Start time (time input) and optional date
    - Timezone select (default local; simple dropdown from common options)
    - "Analyze" button
  - Main area:
    - On click, call `load_playlist_rows(...)`
    - Show summary: number of tracks, total duration
    - Render color-styled table: columns: Index, Song name, Artist, BPM, Song duration, Cumulative duration, Approximate time
    - Provide CSV export button (use `to_csv` + `st.download_button`)
  - Cache:
    - Use `@st.cache_data` for `(playlist_id)` keyed data to speed re-runs
    - "Refresh data" button to bypass cache

- Acceptance Criteria:
  - Users can paste a public playlist URL, select start time, and see a table
  - Table reflects correct cumulative and approximate times
  - Color scales visible for BPM and duration

---

## Step 9 — Robustness & Errors

**Goal**: Ensure helpful messages and resilience.

- Add explicit error messaging for:

  - Invalid/empty playlist URL or ID
  - Missing Spotify credentials
  - HTTP errors, rate limits (suggest retry)
  - No tracks or missing audio features
  - Timezone parsing issues

- Acceptance Criteria:
  - UI shows friendly `st.error` messages with actionable next steps
  - Retries applied for transient network/429 errors

---

## Step 10 — CSV/Excel Export

**Goal**: Allow exporting the analyzed table.

- Implement export utilities in `ui/app.py`:

  - CSV: `df.to_csv(index=False)` and `st.download_button("Download CSV", ...)`
  - (Optional) Excel using `to_excel` and `io.BytesIO`

- Acceptance Criteria:
  - CSV export works and matches the visible table rows (excluding color styles)

---

## Step 11 — Manual QA Checklist

**Goal**: Validate correctness and UX.

- Scenarios:

  - Short playlist (<100 tracks)
  - Long playlist (>100 tracks) — pagination and 100-feature batches
  - Missing BPM track(s)
  - Start time near midnight (rollover)
  - Timezone other than local
  - Refresh cache behavior

- Acceptance Criteria:
  - All scenarios produce correct cumulative timing and stable UI

---

## Step 12 — Performance & Caching

**Goal**: Keep interactions snappy for local use.

- Use `@st.cache_data` for playlist tracks and audio features keyed by playlist ID
- Cache invalidation via "Refresh"
- Batch `audio_features` requests up to 100 IDs per call

- Acceptance Criteria:
  - Re-running the same playlist with unchanged inputs is fast (<1s after initial)

---

## Step 13 — Packaging & Run Instructions

**Goal**: Ensure the app is trivial to start locally.

- Update `README.md` with:

  - How to create a Spotify app and retrieve Client ID/Secret
  - How to create `.env` from `.env.example`
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
  - `streamlit run ui/app.py`

- Acceptance Criteria:
  - Fresh machine can follow steps and see the app running

---

## Step 14 — Nice-to-Haves (Defer)

These are optional and should not block the core tool.

- Sortable columns and per-column filters
- Histograms for BPM and durations
- Save/load presets for start time per playlist
- Dark mode styling
- Offline cache to `data/` as JSON for repeat analyses

---

## Data Contracts

- Input: Public Spotify playlist URL or ID

  - Examples: `https://open.spotify.com/playlist/<id>`, `spotify:playlist:<id>`, `<id>`

- Output Table Columns:

  - Index (1-based)
  - Song name (string)
  - Artist (comma-separated string)
  - BPM (float or blank)
  - Song duration (mm:ss)
  - Cumulative duration (mm:ss)
  - Approximate time (HH:MM, local or selected timezone)

- Stats (for color scaling):
  - `min_bpm`, `max_bpm`
  - `min_duration_ms`, `max_duration_ms`
  - `total_duration_ms`

---

## Implementation Handoffs per Step

Each step should deliver:

- New/updated files
- Docstring-level documentation for key functions
- Minimal smoke test (manual or lightweight script)
- Acceptance criteria satisfied

---

## Risks & Mitigations

- Spotify rate limits (429): use tenacity retries with backoff
- Missing BPM for some tracks: show blank BPM and neutral color
- Day rollover correctness: unit-test with start near midnight
- Timezone mismatch: default to local, allow override

---

## Done Definition (Core)

- Paste a public playlist URL, choose start time, click Analyze
- See a color-scaled table with correct cumulative and approximate times
- Export CSV
- Reasonable performance with caching
