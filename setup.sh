#!/bin/bash

echo "🚀 Setting up Smart Document Q&A Agent..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/documents
mkdir -p data/vectorstore
mkdir -p data/logs

# Create .gitkeep files
touch data/documents/.gitkeep
touch data/vectorstore/.gitkeep
touch data/logs/.gitkeep

# Setup backend
echo "🐍 Setting up backend..."
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download spacy model
python -m spacy download en_core_web_lg

# Copy .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Please edit backend/.env and add your GEMINI_API_KEY"
fi

cd ..

# Setup frontend
echo "⚛️  Setting up frontend..."
cd frontend
npm install
cd ..

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Get your Gemini API key from https://aistudio.google.com/app/apikey"
echo "2. Edit backend/.env and add your GEMINI_API_KEY"
echo "3. Run 'bash start.sh' to start the application"
echo ""