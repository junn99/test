#!/bin/bash
# Email Assistant Agent - Quick Start Script

echo "=================================="
echo "Email Assistant Agent - Quick Start"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "Please edit .env file and add your API keys:"
    echo "  - OPENAI_API_KEY or ANTHROPIC_API_KEY"
    echo ""
    read -p "Press Enter to continue after editing .env file..."
fi

# Check if credentials.json exists
if [ ! -f "credentials.json" ]; then
    echo ""
    echo "⚠️  credentials.json not found!"
    echo ""
    echo "Please download credentials.json from Google Cloud Console:"
    echo "  1. Go to https://console.cloud.google.com/"
    echo "  2. Enable Gmail API"
    echo "  3. Create OAuth 2.0 credentials"
    echo "  4. Download credentials.json to this directory"
    echo ""
    read -p "Press Enter to continue after adding credentials.json..."
fi

# Run setup test
echo ""
echo "Running setup test..."
python test_setup.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Setup test passed!"
    echo ""
    echo "Starting Email Assistant Agent..."
    echo "The app will open in your browser at http://localhost:8501"
    echo ""
    streamlit run app.py
else
    echo ""
    echo "✗ Setup test failed. Please fix the errors above."
    exit 1
fi
