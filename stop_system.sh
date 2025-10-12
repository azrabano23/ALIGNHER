#!/bin/bash

# AlignHer Healthcare System Stop Script

echo "🛑 Stopping AlignHer Healthcare System..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Display banner
echo -e "${PURPLE}"
echo "    _    _ _            _   _           "
echo "   / \  | (_) __ _ _ __ | | | | ___ _ __ "
echo "  / _ \ | | |/ _\` | '_ \| |_| |/ _ \ '__|"
echo " / ___ \| | | (_| | | | |  _  |  __/ |   "
echo "/_/   \_\_|_|\__, |_| |_|_| |_|\___|_|   "
echo "             |___/                      "
echo -e "${NC}"
echo -e "${BLUE}Shutting down system...${NC}"
echo ""

# Function to stop process by PID file
stop_process() {
    local pid_file=$1
    local name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${BLUE}🛑 Stopping $name (PID: $pid)...${NC}"
            kill $pid
            sleep 2
            
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${YELLOW}⚠️  Force killing $name...${NC}"
                kill -9 $pid
            fi
            
            echo -e "${GREEN}✅ $name stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  $name process not running${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠️  No PID file found for $name${NC}"
    fi
}

# Stop Phase 1
stop_process "phase1.pid" "Phase 1 (Smart Triage & Scheduling)"

# Stop Phase 2
stop_process "phase2.pid" "Phase 2 (No-Show Prevention)"

# Clean up any remaining processes on the ports
echo -e "${BLUE}🧹 Cleaning up any remaining processes...${NC}"

# Kill any process using port 3000
if lsof -ti:3000 > /dev/null 2>&1; then
    echo -e "${BLUE}   Killing processes on port 3000...${NC}"
    lsof -ti:3000 | xargs kill -9 2>/dev/null
fi

# Kill any process using port 8000
if lsof -ti:8000 > /dev/null 2>&1; then
    echo -e "${BLUE}   Killing processes on port 8000...${NC}"
    lsof -ti:8000 | xargs kill -9 2>/dev/null
fi

# Clean up log files (optional)
read -p "🗑️  Remove log files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f phase1.log phase2.log phase1_install.log phase2_install.log
    echo -e "${GREEN}✅ Log files removed${NC}"
fi

echo ""
echo -e "${GREEN}🏥 AlignHer Healthcare System stopped successfully!${NC}"
echo -e "${BLUE}Thank you for using AlignHer! 💙${NC}"
