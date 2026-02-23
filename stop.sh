#!/bin/bash

echo "🛑 Stopping Smart Document Q&A Agent..."

# Kill processes on ports 8000 and 5173
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

echo "✅ Services stopped"