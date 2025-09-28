# 🎵 Spotify Playlist Timing Analyzer

A lightweight local tool that ingests a public Spotify playlist URL, fetches tracks and computes cumulative timing, and renders a sortable, color-scaled table with an adjustable start time to estimate when each song will play.

## ✨ Features

- **Playlist Analysis**: Analyze any public Spotify playlist
- **Timing Calculations**: View cumulative play times with custom start times
- **Duration Scaling**: Color-coded song duration visualization
- **Timezone Support**: Multiple timezone options for accurate timing
- **CSV Export**: Download analysis results as CSV
- **Caching**: Fast re-analysis of previously loaded playlists

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Spotify Developer Account

## 🌐 Deploy to Streamlit Cloud

1. **Fork this repository** on GitHub
2. **Go to [Streamlit Community Cloud](https://share.streamlit.io/)**
3. **Click "New app"** and connect your GitHub account
4. **Select your forked repository**
5. **Set the main file path to**: `ui/app.py`
6. **Add your Spotify credentials** in the secrets section:
   ```
   spotify_client_id = "your_client_id_here"
   spotify_client_secret = "your_client_secret_here"
   ```
7. **Click "Deploy!"**

Your app will be live at `https://your-username-spotify-playlist-timing-analyzer.streamlit.app`

## 🏠 Local Development

### 1. Create Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click "Create an App"
3. Fill in app name and description
4. Copy the **Client ID** and **Client Secret**

### 2. Setup Environment

```bash
# Clone or download the project
cd spotify-analyzer

# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Credentials

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Spotify credentials
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### 4. Run the Application

**Option A: Quick Start (Recommended)**

```bash
# Use the provided run script
./run_app.sh
```

**Option B: Manual Setup**

```bash
# Activate the virtual environment (if not already active)
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the Streamlit app (with PYTHONPATH to find local modules)
PYTHONPATH=$(pwd) streamlit run ui/app.py
```

The app will open in your browser at `http://localhost:8501`

## 🎯 Usage

1. **Enter Playlist URL**: Paste any public Spotify playlist URL, URI, or ID
2. **Set Start Time**: Choose when you want the playlist to start
3. **Select Timezone**: Pick your preferred timezone for time calculations
4. **Click Analyze**: Watch the magic happen!

The app will display:

- Playlist summary with track count and total duration
- Color-coded table showing timing information
- Downloadable CSV export

## 🎨 Color Coding

- **Duration**: Green (short) → Yellow (medium) → Red (long)

## 🛠️ Development

### Project Structure

```
spotify-analyzer/
├── config/          # Configuration management
├── spotify/         # Spotify API client and playlist processing
├── domain/          # Data models
├── logic/           # Business logic (timing, colors, formatting)
├── ui/              # Streamlit interface
├── requirements.txt # Python dependencies
└── README.md        # This file
```

### Testing Components

```bash
# Test individual modules
python3 -c "from config.settings import get_settings; print('Config OK')"
python3 -c "from spotify.client import SpotifyClient; print('Client OK')"
python3 -c "from logic.timing import compute_cumulative_ms; print('Timing OK')"
```

## 🤝 Contributing

This is a focused tool built according to a specific implementation plan. For enhancements or bug fixes, please check the `plan.md` file for design decisions.

## 📄 License

Built for educational and personal use. Check Spotify's Developer Terms of Service for API usage guidelines.

## 🔧 Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'spotify'"**

   - Use the correct command with PYTHONPATH: `PYTHONPATH=$(pwd) streamlit run ui/app.py`
   - Make sure you're in the project root directory
   - Ensure the virtual environment is activated: `source .venv/bin/activate`

2. **"Invalid playlist URL" error**

   - Ensure the playlist is public on Spotify
   - Try using the full URL format: `https://open.spotify.com/playlist/...`

3. **"Error loading playlist" with credentials**

   - Verify your `.env` file has correct Spotify credentials
   - Check that your Spotify app has the correct permissions

4. **App won't start**
   - Ensure port 8501 is not in use: `lsof -i :8501`
   - Try a different port: `streamlit run ui/app.py --server.port 8502`

## ⚠️ Important Notes

- Only works with **public** Spotify playlists
- Requires valid Spotify API credentials
- Rate limited by Spotify API (but includes automatic retries)
- Local processing only - no data is sent to external servers
