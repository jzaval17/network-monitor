#!/bin/bash
# Network Monitor Ubuntu Setup and Startup Script

set -e

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "=================================================="
echo "  Network Monitor - Ubuntu Setup & Launch"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}✓${NC} Current directory: $(pwd)"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION"
echo ""

# Check if requirements are installed
echo "Checking dependencies..."
if python3 -c "import flask, requests, psutil, schedule" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} All required packages installed"
else
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip3 install -r requirements.txt -q
    echo -e "${GREEN}✓${NC} Dependencies installed"
fi
echo ""

# Check .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓${NC} .env file created"
    echo ""
    echo -e "${YELLOW}Please edit .env to configure:${NC}"
    echo "  - ROUTER_IP (your router's IP address)"
    echo "  - DISCORD_WEBHOOK_URL (if you want alerts)"
    echo ""
fi

# Check logs directory
mkdir -p logs

echo "=================================================="
echo "  Setup Complete! Choose an option:"
echo "=================================================="
echo ""
echo "1) Start Monitor (background monitoring task)"
echo "2) Start Flask App (web dashboard on port 5000)"
echo "3) Start Both (monitor + Flask)"
echo "4) Run Tests"
echo "5) View Status"
echo ""
echo "Usage Examples:"
echo "  ./start-ubuntu.sh 1    # Start monitor"
echo "  ./start-ubuntu.sh 3    # Start both"
echo ""

# If an argument is passed, execute the command
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}No option selected. Run with: ./start-ubuntu.sh <option>${NC}"
    exit 0
fi

case $1 in
    1)
        echo -e "${GREEN}Starting Monitor...${NC}"
        python3 monitor.py
        ;;
    2)
        echo -e "${GREEN}Starting Flask App...${NC}"
        echo "Dashboard: http://localhost:5000"
        python3 app.py
        ;;
    3)
        echo -e "${GREEN}Starting Monitor and Flask App...${NC}"
        echo "Dashboard: http://localhost:5000"
        python3 monitor.py &
        MONITOR_PID=$!
        sleep 2
        python3 app.py
        ;;
    4)
        echo -e "${GREEN}Running tests...${NC}"
        python3 -m pytest tests/ -v
        ;;
    5)
        echo -e "${GREEN}Fetching Network Status...${NC}"
        python3 -c "
from utils import print_status_summary
print_status_summary()
"
        ;;
    *)
        echo -e "${RED}Invalid option: $1${NC}"
        echo "Use: 1, 2, 3, 4, or 5"
        exit 1
        ;;
esac
