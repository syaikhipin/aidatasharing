#!/bin/bash

# AI Share Platform - Proxy Service Startup Script
# This script starts only the proxy services without backend/frontend

echo "🚀 Starting AI Share Platform Proxy Services..."

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to stop process on a specific port
stop_port() {
    local port=$1
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo "🔄 Stopping process on port $port (PID: $pid)..."
        kill -9 $pid 2>/dev/null
        sleep 1
    fi
}

# Stop existing proxy services on our ports
echo "🧹 Cleaning up existing proxy services..."
for port in 10101 10102 10103 10104 10105 10106 10107; do
    if check_port $port; then
        stop_port $port
    fi
done

# Check if MindsDB is running (required for proxy services)
echo "🔍 Checking MindsDB status..."
if ! curl -s "http://localhost:47334/api/status" > /dev/null 2>&1; then
    echo "❌ MindsDB is not running!"
    echo "   Please start MindsDB first using: ./start-mindsdb.sh"
    echo "   Or run the full development environment: ./start-dev.sh"
    exit 1
else
    echo "✅ MindsDB is running"
fi

# Check if backend is running (required for proxy authentication)
echo "🔍 Checking backend status..."
if ! curl -s "http://localhost:8000/health" > /dev/null 2>&1; then
    echo "❌ Backend is not running!"
    echo "   Please start the backend first."
    echo "   Or run the full development environment: ./start-dev.sh"
    exit 1
else
    echo "✅ Backend is running"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the proxy services
echo "🌐 Starting proxy servers on dedicated ports..."
echo ""
echo "Port allocation:"
echo "  - MySQL Proxy:      http://localhost:10101"
echo "  - PostgreSQL Proxy: http://localhost:10102"
echo "  - API Proxy:        http://localhost:10103"
echo "  - ClickHouse Proxy: http://localhost:10104"
echo "  - MongoDB Proxy:    http://localhost:10105"
echo "  - S3 Proxy:         http://localhost:10106"
echo "  - Shared Links:     http://localhost:10107"
echo ""

# Check if the proxy service file exists
if [ ! -f "backend/proxy_server.py" ]; then
    echo "❌ Proxy server file not found: backend/proxy_server.py"
    exit 1
fi

# Start proxy service in background
cd backend
nohup python proxy_server.py > ../logs/proxy_service.log 2>&1 &
PROXY_PID=$!
cd ..

if [ $? -eq 0 ]; then
    echo "✅ Proxy service started with PID: $PROXY_PID"
    echo "📋 Logs available at: logs/proxy_service.log"
    
    # Save PID for easy stopping
    echo $PROXY_PID > proxy_service.pid
    
    # Wait for services to start
    echo "⏳ Waiting for proxy services to initialize..."
    sleep 5
    
    # Test proxy services
    echo ""
    echo "🧪 Testing proxy service health..."
    
    success_count=0
    total_ports=7
    
    for port in 10101 10102 10103 10104 10105 10106 10107; do
        if curl -s --connect-timeout 3 "http://localhost:$port/health" > /dev/null 2>&1; then
            echo "✅ Port $port: Proxy service running"
            ((success_count++))
        else
            echo "❌ Port $port: Proxy service not responding"
        fi
    done
    
    echo ""
    if [ $success_count -eq $total_ports ]; then
        echo "🎉 All proxy services started successfully! ($success_count/$total_ports)"
    elif [ $success_count -gt 0 ]; then
        echo "⚠️  Some proxy services started successfully ($success_count/$total_ports)"
    else
        echo "❌ No proxy services are responding. Check logs/proxy_service.log"
        exit 1
    fi
    
    echo ""
    echo "📖 Usage Examples:"
    echo "  🔗 MySQL Connection:"
    echo "    curl 'http://localhost:10101/dataset_name?token=YOUR_TOKEN'"
    echo ""
    echo "  🔗 PostgreSQL Connection:"
    echo "    curl 'http://localhost:10102/dataset_name?token=YOUR_TOKEN'"
    echo ""
    echo "  🔗 API Connection:"
    echo "    curl 'http://localhost:10103/api_name?token=YOUR_TOKEN'"
    echo ""
    echo "  📊 Health Check:"
    echo "    curl http://localhost:10101/health"
    echo ""
    echo "  🛑 Stop Proxy Services:"
    echo "    ./stop-proxy.sh"
    echo ""
    echo "📋 Log Files:"
    echo "  - Proxy Service: logs/proxy_service.log"
    echo "  - View logs: tail -f logs/proxy_service.log"
    
else
    echo "❌ Failed to start proxy service"
    exit 1
fi