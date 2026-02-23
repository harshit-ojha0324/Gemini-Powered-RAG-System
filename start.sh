#!/bin/bash

echo "🚀 Starting Smart Document Q&A Agent..."

# Check if .env exists
if [ ! -f backend/.env ]; then
    echo "❌ backend/.env not found. Run setup.sh first!"
    exit 1
fi

# Kill anything already running on port 8000
if lsof -ti :8000 &>/dev/null; then
    echo "⚠️  Port 8000 in use. Killing existing process..."
    lsof -ti :8000 | xargs kill -9
    sleep 1
fi

# Start backend in background
echo "🐍 Starting backend on port 8000..."
cd backend
source venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "⚛️  Starting frontend on port 5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Application is running!"
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🤖 Powered by: Google Gemini 2.0 Flash"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for Ctrl+C
trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait