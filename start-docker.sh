#!/bin/bash

echo "🐳 Starting with Docker..."

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Please edit .env and add your GEMINI_API_KEY"
    exit 1
fi

# Start services
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "✅ Services started!"
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🤖 Powered by: Google Gemini 2.0 Flash"
echo ""
echo "View logs: docker-compose logs -f"
echo "Stop services: docker-compose down"