#!/bin/bash
# AI Share Platform - Development Startup Script

echo "🚀 Starting AI Share Platform Development Environment..."

# Check if conda environment exists and activate it
if conda info --envs | grep -q "aishare-platform"; then
    echo "📦 Activating conda environment: aishare-platform"
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate aishare-platform
else
    echo "⚠️  Conda environment 'aishare-platform' not found"
    echo "   Create it with: conda create -n aishare-platform python=3.9"
    echo "   Then run: conda activate aishare-platform && pip install -r backend/requirements.txt"
fi

# Create necessary directories
mkdir -p storage/uploads storage/documents storage/logs logs

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
echo "   Admin: admin@aishare.com / admin123"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID; exit 0' INT
wait
