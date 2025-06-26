#!/bin/bash

# AI Share Platform Development Startup Script

echo "🚀 Starting AI Share Platform Development Environment..."

# Store the root directory
ROOT_DIR=$(pwd)

# Function to kill processes on script exit
cleanup() {
    echo ""
    echo "🛑 Shutting down development servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "  ✅ Backend stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "  ✅ Frontend stopped"
    fi
    # Kill any remaining processes on ports 8000 and 3000
    pkill -f "python.*start.py" 2>/dev/null
    pkill -f "next.*dev" 2>/dev/null
    cd "$ROOT_DIR"
    exit
}

# Set up cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Check if conda environment exists
if ! conda info --envs | grep -q "aishare-platform"; then
    echo "❌ Conda environment 'aishare-platform' not found. Please create it first."
    echo "   Run: conda create -n aishare-platform python=3.9"
    exit 1
fi

# Check if backend directory exists
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found. Make sure you're in the project root."
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "❌ Frontend directory not found. Make sure you're in the project root."
    exit 1
fi

# Start Backend
echo "🔧 Starting Backend (FastAPI)..."
cd "$ROOT_DIR/backend"

# Initialize conda for this shell session
eval "$(conda shell.bash hook)"

# Activate conda environment and start backend
if conda activate aishare-platform; then
    echo "  ✅ Conda environment activated"
    # Check if start.py exists
    if [ ! -f "start.py" ]; then
        echo "❌ start.py not found in backend directory"
        exit 1
    fi
    
    python start.py &
    BACKEND_PID=$!
    echo "  ✅ Backend started on http://localhost:8000 (PID: $BACKEND_PID)"
else
    echo "❌ Failed to activate conda environment 'aishare-platform'"
    exit 1
fi

# Wait a moment for backend to start
sleep 3

# Start Frontend  
echo "🎨 Starting Frontend (Next.js)..."
cd "$ROOT_DIR/frontend"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found in frontend directory"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!
echo "  ✅ Frontend started on http://localhost:3000 (PID: $FRONTEND_PID)"

echo ""
echo "🎉 Development environment is ready!"
echo "📖 Backend API docs: http://localhost:8000/docs"
echo "🌐 Frontend: http://localhost:3000"
echo "👤 Default admin: admin@example.com / admin123"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for both processes to complete (or be interrupted)
wait $BACKEND_PID $FRONTEND_PID 