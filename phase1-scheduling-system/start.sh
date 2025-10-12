#!/bin/bash

# Phase 1: Smart Triage & Scheduling System Startup Script

echo "🏥 Starting Phase 1: Smart Triage & Scheduling System..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cat > .env << EOF
# Phase 1 Configuration
DATABASE_URL=file://storage/
PHASE2_API_URL=http://localhost:8000

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# AI/ML Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
TRIAGE_PROTOCOLS_FILE=data/triage_protocols.csv

# Google Calendar Integration (Optional)
GOOGLE_CALENDAR_CREDENTIALS_FILE=credentials/google_calendar.json

# Logging
LOG_LEVEL=INFO
EOF
    echo "⚠️  Please update .env with your actual configuration"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p storage data credentials logs

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Copy triage protocols if available
if [ -f "/Users/gowri/Downloads/Copy of OBGYNSchedule Advisor 07-17-25 - Smart Phrases.csv" ]; then
    echo "📊 Copying triage protocols..."
    cp "/Users/gowri/Downloads/Copy of OBGYNSchedule Advisor 07-17-25 - Smart Phrases.csv" data/triage_protocols.csv
fi

# Initialize storage files
echo "🗄️  Initializing storage..."
touch storage/users.txt
touch storage/doctors.txt
touch storage/patients.txt
touch storage/appointments.txt
touch storage/triage_assessments.txt

# Start the application
echo "🚀 Starting Phase 1 application..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload

echo "✅ Phase 1 system started successfully!"
echo "📊 API Documentation: http://localhost:3000/docs"
echo "🏥 Health Check: http://localhost:3000/health"
echo "🔗 Integration with Phase 2: http://localhost:8000"
