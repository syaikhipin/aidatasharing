#!/bin/bash

# AI Share Platform - Dependencies Installation Script
# This script installs all required dependencies for the development environment

set -e  # Exit on any error

echo "🚀 Installing AI Share Platform Dependencies..."
echo "================================================"

# Activate conda environment
echo "📦 Activating conda environment: aishare-platform"
if conda info --envs | grep -q "aishare-platform"; then
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate aishare-platform
    echo "✅ Activated conda environment: aishare-platform"
else
    echo "❌ Conda environment 'aishare-platform' not found. Please create it first."
    echo "   Run: conda create -n aishare-platform python=3.9"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python installation
echo "📋 Checking Python installation..."
if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed. Please install Python 3 first."
    exit 1
fi
echo "✅ Python 3 found: $(python3 --version)"

# Check Node.js installation
echo "📋 Checking Node.js installation..."
if ! command_exists node; then
    echo "❌ Node.js is required but not installed. Please install Node.js first."
    exit 1
fi
echo "✅ Node.js found: $(node --version)"

# Check npm installation
echo "📋 Checking npm installation..."
if ! command_exists npm; then
    echo "❌ npm is required but not installed. Please install npm first."
    exit 1
fi
echo "✅ npm found: $(npm --version)"

# Install Python dependencies for backend
echo "📦 Installing Python dependencies..."
cd backend
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    echo "✅ Python dependencies installed"
else
    echo "❌ requirements.txt not found in backend directory"
    exit 1
fi
cd ..

# Install Node.js dependencies for frontend
echo "📦 Installing Node.js dependencies..."
cd frontend
if [ -f "package.json" ]; then
    npm install
    echo "✅ Node.js dependencies installed"
else
    echo "❌ package.json not found in frontend directory"
    exit 1
fi
cd ..

# Install MindsDB separately to avoid conflicts
echo "🧠 Installing MindsDB (as wrapper only)..."
if [ -f "./install-mindsdb.sh" ]; then
    echo "📦 Using dedicated MindsDB installation script..."
    chmod +x ./install-mindsdb.sh
    if ./install-mindsdb.sh; then
        echo "✅ MindsDB installation completed successfully"
    else
        echo "⚠️  MindsDB installation script had issues"
        echo "   The application will work as a wrapper without local MindsDB."
        echo "   You can use external MindsDB instances or Docker:"
        echo "   docker run -p 47334:47334 mindsdb/mindsdb"
    fi
else
    echo "📦 Skipping MindsDB installation (install-mindsdb.sh not found)"
    echo "   The application will work as a wrapper."
    echo "   To install MindsDB later, run: ./install-mindsdb.sh"
fi

# Install Playwright browsers (optional for testing)
echo "📦 Installing Playwright browsers (optional)..."
cd frontend
npm install @playwright/test
npx playwright install
echo "✅ Playwright browsers installed"
cd ..

echo ""
echo "🎉 All dependencies installed successfully!"
echo "================================================"
echo "You can now run the development environment with:"
echo "  ./start-dev.sh"
echo ""
echo "To stop the development environment:"
echo "  ./stop-dev.sh"
echo ""