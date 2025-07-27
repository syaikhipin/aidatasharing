#!/bin/bash

# MindsDB Multi-Port Proxy Service Startup Script

echo "🚀 Starting MindsDB Multi-Port Proxy Service..."

# Stop any existing proxy services
./stop-simple-proxy.sh 2>/dev/null
./stop-unified-proxy.sh 2>/dev/null

# Check if MindsDB is running
echo "🔍 Checking MindsDB status..."
if ! curl -s "http://localhost:47334/api/status" > /dev/null; then
    echo "⚠️  MindsDB not running. Starting MindsDB..."
    ./start-mindsdb.sh
    sleep 5
else
    echo "✅ MindsDB is running"
fi

# Check if backend is running
echo "🔍 Checking backend status..."
if ! curl -s "http://localhost:8000/health" > /dev/null; then
    echo "⚠️  Backend not running. Starting backend..."
    cd backend
    nohup python -m uvicorn main:app --reload --port 8000 --host 0.0.0.0 > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid
    cd ..
    sleep 3
    echo "✅ Backend started with PID: $BACKEND_PID"
else
    echo "✅ Backend is running"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the MindsDB proxy service
echo "🌐 Starting MindsDB proxy servers..."
echo "Port allocation:"
echo "  - MySQL: http://localhost:10101"
echo "  - PostgreSQL: http://localhost:10102"
echo "  - API: http://localhost:10103"
echo "  - ClickHouse: http://localhost:10104"
echo "  - MongoDB: http://localhost:10105"
echo "  - S3: http://localhost:10106"
echo "  - Shared Links: http://localhost:10107"
echo ""

# Start proxy service in background
nohup python mindsdb_proxy_service.py > logs/mindsdb_proxy.log 2>&1 &
PROXY_PID=$!

echo "✅ MindsDB proxy service started with PID: $PROXY_PID"
echo "📋 Logs available at: logs/mindsdb_proxy.log"
echo "🛑 To stop: kill $PROXY_PID"

# Save PID for easy stopping
echo $PROXY_PID > mindsdb_proxy.pid

# Wait for services to start
sleep 5

# Test proxy services
echo ""
echo "🧪 Testing proxy services..."

for port in 10101 10102 10103 10104 10105 10106 10107; do
    if curl -s "http://localhost:$port/health" > /dev/null; then
        echo "✅ Port $port: OK"
    else
        echo "❌ Port $port: Failed"
    fi
done

echo ""
echo "🎉 MindsDB Multi-Port Proxy Service setup complete!"
echo ""
echo "📖 Usage examples:"
echo "  🌐 MySQL Proxy (Port 10101):"
echo "    curl 'http://localhost:10101/Test%20DB%20Unipa%20Dataset?token=0627b5b4afdba49bb348a870eb152e86'"
echo ""
echo "  🌐 PostgreSQL Proxy (Port 10102):"
echo "    curl 'http://localhost:10102/PostgreSQL_DB?token=YOUR_TOKEN'"
echo ""
echo "  🌐 API Proxy (Port 10103):"
echo "    curl 'http://localhost:10103/API_NAME?token=YOUR_TOKEN'"
echo ""
echo "  📊 Health Checks:"
echo "    curl http://localhost:10101/health"
echo ""
echo "  🔧 Stop Services:"
echo "    ./stop-mindsdb-proxy.sh"
echo ""
echo "📋 Logs available at:"
echo "  - MindsDB Proxy: logs/mindsdb_proxy.log"
echo "  - Backend: logs/backend.log"
echo "  - MindsDB: logs/mindsdb.log"