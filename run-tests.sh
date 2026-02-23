#!/bin/bash

echo "🧪 Running tests..."

cd backend
source venv/bin/activate

# Run pytest with coverage
pytest --cov=. --cov-report=html --cov-report=term -v

echo ""
echo "✅ Tests complete!"
echo "📊 View coverage report: backend/htmlcov/index.html"

cd ..