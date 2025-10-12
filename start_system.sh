#!/bin/bash

# AlignHer Healthcare System Startup Script
# Complete AI-powered healthcare solution

echo "🏥 Starting AlignHer Healthcare System..."
echo "=" * 50

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
echo -e "${BLUE}Complete Healthcare System - AI Powered${NC}"
echo ""

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}⚠️  Port $1 is already in use${NC}"
        return 1
    else
        return 0
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${BLUE}⏳ Waiting for $name to be ready...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $name is ready!${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $name failed to start within timeout${NC}"
    return 1
}

# Check prerequisites
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python 3 found${NC}"

# Check ports
echo -e "${BLUE}🔌 Checking ports...${NC}"
check_port 3000 || echo -e "${YELLOW}   Phase 1 port (3000) in use - will attempt to start anyway${NC}"
check_port 8000 || echo -e "${YELLOW}   Phase 2 port (8000) in use - will attempt to start anyway${NC}"

# Install dependencies for Phase 1
echo -e "${BLUE}📦 Installing Phase 1 dependencies...${NC}"
cd phase1-scheduling-system

# Install required packages
pip install fastapi uvicorn python-multipart pydantic python-dotenv httpx python-jose passlib bcrypt pandas numpy sentence-transformers faiss-cpu email-validator > ../phase1_install.log 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Phase 1 dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  Some dependencies may have failed to install (check phase1_install.log)${NC}"
fi

# Initialize storage
echo -e "${BLUE}🗄️  Initializing storage...${NC}"
mkdir -p storage data
touch storage/users.txt storage/doctors.txt storage/patients.txt storage/appointments.txt storage/triage_assessments.txt

# Start Phase 1
echo -e "${BLUE}🚀 Starting Phase 1: Smart Triage & Scheduling...${NC}"
python -m uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload > ../phase1.log 2>&1 &
PHASE1_PID=$!
echo $PHASE1_PID > ../phase1.pid

cd ..

# Wait for Phase 1 to be ready
if wait_for_service "http://localhost:3000/health" "Phase 1"; then
    echo -e "${GREEN}✅ Phase 1 started successfully (PID: $PHASE1_PID)${NC}"
else
    echo -e "${RED}❌ Phase 1 failed to start${NC}"
    kill $PHASE1_PID 2>/dev/null
    exit 1
fi

# Try to start Phase 2 (optional)
echo -e "${BLUE}🎯 Attempting to start Phase 2: No-Show Prevention...${NC}"
if [ -d "patient-noshow-prevention" ]; then
    cd patient-noshow-prevention
    
    # Check if PostgreSQL is available
    if command -v psql &> /dev/null; then
        echo -e "${BLUE}📦 Installing Phase 2 dependencies...${NC}"
        pip install -r requirements.txt > ../phase2_install.log 2>&1
        
        if [ $? -eq 0 ]; then
            echo -e "${BLUE}🚀 Starting Phase 2...${NC}"
            python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../phase2.log 2>&1 &
            PHASE2_PID=$!
            echo $PHASE2_PID > ../phase2.pid
            
            # Wait for Phase 2
            if wait_for_service "http://localhost:8000/health" "Phase 2"; then
                echo -e "${GREEN}✅ Phase 2 started successfully (PID: $PHASE2_PID)${NC}"
            else
                echo -e "${YELLOW}⚠️  Phase 2 failed to start (PostgreSQL may not be configured)${NC}"
                kill $PHASE2_PID 2>/dev/null
            fi
        else
            echo -e "${YELLOW}⚠️  Phase 2 dependencies failed to install${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  PostgreSQL not found - Phase 2 will not start${NC}"
        echo -e "${BLUE}   Phase 1 works independently with full functionality${NC}"
    fi
    
    cd ..
else
    echo -e "${YELLOW}⚠️  Phase 2 directory not found${NC}"
fi

# Display system information
echo ""
echo -e "${GREEN}🎉 AlignHer Healthcare System Started Successfully!${NC}"
echo "=" * 60
echo -e "${BLUE}📊 System Information:${NC}"
echo -e "   🏥 Main Interface:          ${GREEN}http://localhost:3000${NC}"
echo -e "   🧪 Simple Test Interface:   ${GREEN}http://localhost:3000/static/simple.html${NC}"
echo -e "   📚 API Documentation:       ${GREEN}http://localhost:3000/docs${NC}"
echo -e "   📋 System Health:           ${GREEN}http://localhost:3000/health${NC}"

if [ ! -z "$PHASE2_PID" ] && ps -p $PHASE2_PID > /dev/null 2>&1; then
    echo -e "   🎯 No-Show Prevention:      ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "   📋 Phase 2 Health:          ${GREEN}http://localhost:8000/health${NC}"
fi

echo ""
echo -e "${BLUE}🔧 Process Information:${NC}"
echo -e "   Phase 1 PID: $PHASE1_PID (Log: phase1.log)"
if [ ! -z "$PHASE2_PID" ] && ps -p $PHASE2_PID > /dev/null 2>&1; then
    echo -e "   Phase 2 PID: $PHASE2_PID (Log: phase2.log)"
fi

echo ""
echo -e "${BLUE}🎯 AlignHer Features:${NC}"
echo -e "   ✅ AI-Powered Triage Assessment"
echo -e "   ✅ Intelligent Provider Matching"
echo -e "   ✅ Automated Appointment Scheduling"
echo -e "   ✅ Modern Web Interface"
echo -e "   ✅ Real-time Analytics Dashboard"
if [ ! -z "$PHASE2_PID" ] && ps -p $PHASE2_PID > /dev/null 2>&1; then
    echo -e "   ✅ No-Show Risk Prediction"
    echo -e "   ✅ Tiered Intervention Campaigns"
    echo -e "   ✅ Complete System Integration"
fi

echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo -e "   1. Open ${GREEN}http://localhost:3000${NC} in your browser"
echo -e "   2. Try the simple test: ${GREEN}http://localhost:3000/static/simple.html${NC}"
echo -e "   3. Register doctors and patients"
echo -e "   4. Perform triage assessments"
echo -e "   5. Schedule appointments"

echo ""
echo -e "${BLUE}🛑 To stop AlignHer:${NC}"
echo -e "   Run: ${YELLOW}./stop_system.sh${NC}"
echo -e "   Or manually: ${YELLOW}kill $PHASE1_PID${NC}"

echo ""
echo -e "${GREEN}🏥 AlignHer is ready to revolutionize healthcare!${NC}"
