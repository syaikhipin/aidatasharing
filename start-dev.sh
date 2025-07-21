#!/bin/bash

# AI Share Platform - Development Environment Startup Script
# This script starts all required services for the development environment
# Run ./install-deps.sh first to install all dependencies

set -e  # Exit on any error

echo "🚀 Starting AI Share Platform Development Environment..."
echo "===================================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    lsof -i :"$1" >/dev/null 2>&1
}

# Function to wait for service to be ready
wait_for_service() {
    local url="$1"
    local service_name="$2"
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts - $service_name not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to start within expected time"
    return 1
}

# Activate conda environment
echo "📦 Activating conda environment: aishare-platform"
if conda info --envs | grep -q "aishare-platform"; then
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate aishare-platform
    echo "✅ Activated conda environment: aishare-platform"
else
    echo "❌ Conda environment 'aishare-platform' not found. Please create it first."
    echo "   Run: conda create -n aishare-platform python=3.10"
    echo "   Then run: ./install-deps.sh"
    exit 1
fi

# Create necessary directories
mkdir -p storage/uploads storage/documents storage/logs logs

# MindsDB checking and startup removed as requested

# Start backend in background
echo "🔧 Starting backend server..."
(cd backend && python start.py) &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend in background  
echo "🎨 Starting frontend server..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo "✅ Development environment started!"
echo "   Backend: http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   Admin: admin@example.com / admin123"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT
wait
