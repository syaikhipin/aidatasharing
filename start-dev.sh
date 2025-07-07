#!/bin/bash

# AI Share Platform Development Startup Script

echo "🚀 Starting AI Share Platform Development Environment..."

# Store the root directory
ROOT_DIR=$(pwd)

# Function to kill processes on script exit
cleanup() {
    echo ""
    echo "🛑 Shutting down development servers..."
    if [ ! -z "$MINDSDB_PID" ]; then
        kill $MINDSDB_PID 2>/dev/null
        echo "  ✅ MindsDB stopped"
    fi
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "  ✅ Backend stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "  ✅ Frontend stopped"
    fi
    # Kill any remaining processes on ports 47334, 8000 and 3000
    pkill -f "python.*mindsdb" 2>/dev/null
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

# Initialize conda for this shell session
eval "$(conda shell.bash hook)"

# Activate conda environment
if conda activate aishare-platform; then
    echo "  ✅ Conda environment activated"
else
    echo "❌ Failed to activate conda environment 'aishare-platform'"
    exit 1
fi

# Start MindsDB
echo "🧠 Starting MindsDB..."
cd "$ROOT_DIR/backend"

# Check if MindsDB is already installed, if not install it with handlers
if ! python -c "import mindsdb" 2>/dev/null; then
    echo "📦 Installing MindsDB with Google Gemini and File handlers..."
    pip install "mindsdb[google-gemini,files]" || {
        echo "⚠️  Failed to install with handlers, installing base MindsDB..."
        pip install mindsdb
    }
fi

# Suppress Pydantic warnings from MindsDB
export PYTHONWARNINGS="ignore::UserWarning:pydantic._internal._fields"

# Start MindsDB in background
python -m mindsdb --api http,mysql --no_studio &
MINDSDB_PID=$!
echo "  ✅ MindsDB started on http://127.0.0.1:47334 (PID: $MINDSDB_PID)"

# Wait for MindsDB to be ready
echo "⏳ Waiting for MindsDB to initialize..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:47334/api/status > /dev/null 2>&1; then
        echo "  ✅ MindsDB is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "  ⚠️  MindsDB taking longer than expected to start, continuing anyway..."
        break
    fi
    sleep 2
done

# Start Backend
echo "🔧 Starting Backend (FastAPI)..."

# Check if start.py exists
if [ ! -f "start.py" ]; then
    echo "❌ start.py not found in backend directory"
    exit 1
fi

python start.py &
BACKEND_PID=$!
echo "  ✅ Backend started on http://localhost:8000 (PID: $BACKEND_PID)"

# Wait a moment for backend to start
sleep 3

# Start Frontend  
echo "🎨 Starting Frontend (Next.js)..."
echo "-" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd "$ROOT_DIR/frontend"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found in frontend directory"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    echo "   This may take a few minutes on first run..."
    npm install
    if [ $? -eq 0 ]; then
        echo "   ✅ Dependencies installed successfully"
    else
        echo "   ❌ Failed to install dependencies"
        exit 1
    fi
fi

echo "🚀 Launching Next.js development server..."
npm run dev &
FRONTEND_PID=$!
echo "  ✅ Frontend started on http://localhost:3000 (PID: $FRONTEND_PID)"
echo "  📱 Frontend Features:"
echo "     🔐 User Authentication & Registration"
echo "     🏢 Organization Management"
echo "     📊 Dataset Upload & Management"
echo "     🤖 AI Model Creation & Chat"
echo "     📈 Analytics Dashboard"
echo "     🔗 Data Sharing Interface"
echo "     🛠️ Admin Panel"
echo "-" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "🎉━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━🎉"
echo "🚀 AI SHARE PLATFORM - DEVELOPMENT ENVIRONMENT READY!"
echo "🎉━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━🎉"
echo ""
echo "📍 SERVICE ENDPOINTS:"
echo "   🧠 MindsDB Server:    http://127.0.0.1:47334"
echo "   🔧 Backend API:       http://localhost:8000"
echo "   📖 API Documentation: http://localhost:8000/docs"
echo "   🔍 ReDoc:             http://localhost:8000/redoc"
echo "   🌐 Frontend App:      http://localhost:3000"
echo ""
echo "🔑 DEFAULT CREDENTIALS:"
echo "   👤 Admin User: admin@example.com"
echo "   🔒 Password:   admin123"
echo ""
echo "📊 SYSTEM STATUS:"
echo "   🧠 MindsDB:  $(if curl -s http://127.0.0.1:47334/api/status >/dev/null 2>&1; then echo "✅ Running"; else echo "⚠️ Check status"; fi)"
echo "   🔧 Backend:  $(if curl -s http://localhost:8000/health >/dev/null 2>&1; then echo "✅ Running"; else echo "⚠️ Starting..."; fi)"
echo "   🌐 Frontend: $(if curl -s http://localhost:3000 >/dev/null 2>&1; then echo "✅ Running"; else echo "⚠️ Starting..."; fi)"
echo ""
echo "🛠️ AVAILABLE FEATURES:"
echo "   🔐 Multi-organization authentication"
echo "   📊 Advanced dataset management"
echo "   🤖 AI model creation with Gemini"
echo "   💬 Dataset-specific AI chat"
echo "   📈 Real-time analytics"
echo "   🔗 Secure data sharing"
echo "   🛠️ Administrative tools"
echo ""
echo "🎯 QUICK START:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Register a new account or use admin credentials"
echo "   3. Create an organization"
echo "   4. Upload a dataset"
echo "   5. Chat with your data using AI!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  Press Ctrl+C to stop all services gracefully"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Wait for all processes to complete (or be interrupted)
wait $MINDSDB_PID $BACKEND_PID $FRONTEND_PID 