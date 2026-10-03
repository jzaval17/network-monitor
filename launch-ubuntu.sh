#!/bin/bash
# ============================================================
# Network Monitor - Ubuntu/WSL Quick Launch
# ============================================================

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR" || exit 1

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "============================================================"
echo "  Network Monitor - Ubuntu Quick Start"
echo "============================================================"
echo -e "${NC}"
echo ""

# Check dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"
pip3 install -q -r requirements.txt 2>&1 | grep -E "Successfully installed|ERROR" || true

echo -e "${GREEN}✓ Setup complete!${NC}"
echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}Starting Network Monitor...${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo "📊 Dashboard URL: http://localhost:5000"
echo "📝 Monitor logs: tail -f logs/monitor.log"
echo "📝 Flask logs:   tail -f logs/app.log"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Create logs directory
mkdir -p logs

# Start monitor in background with logging
python3 monitor.py >> logs/monitor.log 2>&1 &
MONITOR_PID=$!
echo -e "${GREEN}✓ Monitor started (PID: $MONITOR_PID)${NC}"

# Give monitor time to initialize
sleep 2

# Start Flask app in foreground
echo ""
echo -e "${GREEN}✓ Starting Flask dashboard...${NC}"
echo ""

python3 app.py 2>&1 | tee -a logs/app.log

# Cleanup on exit
trap "kill $MONITOR_PID 2>/dev/null" EXIT
