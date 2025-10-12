#!/bin/bash

# Patient No-Show Prevention System Startup Script

echo "🏥 Starting Patient No-Show Prevention System..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your actual credentials before running in production"
fi

# Start database services
echo "🗄️  Starting database services..."
docker-compose up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run database migrations
echo "🔄 Running database migrations..."
# alembic upgrade head

# Start Celery worker in background
echo "🔧 Starting Celery worker..."
celery -A app.tasks worker --loglevel=info --detach

# Start Celery beat scheduler in background
echo "⏰ Starting Celery beat scheduler..."
celery -A app.tasks beat --loglevel=info --detach

# Start the main application
echo "🚀 Starting FastAPI application..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo "✅ System started successfully!"
echo "📊 API Documentation: http://localhost:8000/docs"
echo "🏥 Health Check: http://localhost:8000/health"
