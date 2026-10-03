#!/bin/bash
# Quick start Network Monitor on Ubuntu

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

echo "=================================================="
echo "  Network Monitor - Quick Start"
echo "=================================================="
echo ""

# Install dependencies silently
echo "Installing dependencies..."
pip3 install -q -r requirements.txt 2>&1 | grep -v "WARNING" || true

echo "✓ Setup complete!"
echo ""
echo "Starting Monitor + Dashboard..."
echo "Dashboard will be at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start both processes
python3 monitor.py &
MONITOR_PID=$!

sleep 2

python3 app.py &
APP_PID=$!

# Wait for both processes
wait $MONITOR_PID $APP_PID
