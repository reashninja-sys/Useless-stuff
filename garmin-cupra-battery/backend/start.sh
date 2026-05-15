#!/data/data/com.termux/files/usr/bin/bash
# Start the Cupra battery server.
# Keep this Termux session open, or run it in the background with:
#   bash start.sh &

cd "$(dirname "$0")"

if [ ! -f .env ]; then
    echo "ERROR: .env not found. Copy .env.example and fill it in first."
    exit 1
fi

echo "Starting Cupra battery server..."
python3 server.py
