#!/bin/bash

# Spotify Playlist Analyzer - Run Script
# This script ensures the app runs with the correct Python path

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies if needed
echo "Checking dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Run the Streamlit app with correct PYTHONPATH
echo "Starting Spotify Playlist Analyzer..."
echo "The app will open at: http://localhost:8501"
echo "Press Ctrl+C to stop the app"
echo ""

PYTHONPATH=$(pwd) streamlit run ui/app.py
