#!/bin/bash

# MindsDB Multi-Port Proxy Service Stop Script

echo "🛑 Stopping MindsDB Multi-Port Proxy Service..."

# Stop MindsDB proxy service
if [ -f "mindsdb_proxy.pid" ]; then
    PROXY_PID=$(cat mindsdb_proxy.pid)
    echo "🔄 Stopping MindsDB proxy service (PID: $PROXY_PID)..."
    kill $PROXY_PID 2>/dev/null
    rm -f mindsdb_proxy.pid
    echo "✅ MindsDB proxy service stopped"
else
    echo "⚠️  No MindsDB proxy PID file found"
    # Try to find and kill the process
    PROXY_PID=$(pgrep -f "mindsdb_proxy_service.py")
    if [ ! -z "$PROXY_PID" ]; then
        echo "🔍 Found MindsDB proxy process (PID: $PROXY_PID), stopping..."
        kill $PROXY_PID 2>/dev/null
        echo "✅ MindsDB proxy service stopped"
    fi
fi

# Stop backend if we started it
if [ -f "backend.pid" ]; then
    BACKEND_PID=$(cat backend.pid)
    echo "🔄 Stopping backend service (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    rm -f backend.pid
    echo "✅ Backend service stopped"
fi

# Check if any processes are still running on our ports
echo "🔍 Checking for remaining processes on proxy ports..."

for port in 10101 10102 10103 10104 10105 10106 10107; do
    PID=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo "🔄 Stopping process on port $port (PID: $PID)..."
        kill $PID 2>/dev/null
    fi
done

# Wait for processes to stop
sleep 2

# Verify ports are free
echo "🧪 Verifying ports are free..."
ACTIVE_PORTS=""
for port in 10101 10102 10103 10104 10105 10106 10107; do
    if lsof -ti:$port > /dev/null 2>&1; then
        ACTIVE_PORTS="$ACTIVE_PORTS $port"
    fi
done

if [ -z "$ACTIVE_PORTS" ]; then
    echo "✅ All proxy ports are now free"
else
    echo "⚠️  Some ports are still in use: $ACTIVE_PORTS"
    echo "💡 You may need to wait a moment or manually kill processes"
fi

echo "🎉 MindsDB Multi-Port Proxy Service stopped!"
echo ""
echo "📋 Log files preserved at:"
echo "  - logs/mindsdb_proxy.log"
echo "  - logs/backend.log"
echo "  - logs/mindsdb.log"