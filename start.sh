#!/bin/bash

# N8N Dashboard Start Script
echo "🚀 Starting N8N Dashboard Setup..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📋 Installing required packages..."
pip install -r requirements.txt

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo "✅ All packages installed successfully!"
    echo ""
    echo "🌟 Starting Flask application..."
    echo "📱 Dashboard will be available at: http://127.0.0.1:3000"
    echo "🔓 Public form available at: http://127.0.0.1:3000/prozess-anfrage"
    echo "🔐 Admin login: password = admin123"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo "----------------------------------------"
    
    # Start the Flask application
    python app.py
else
    echo "❌ Error installing packages. Please check the requirements.txt file."
    exit 1
fi
