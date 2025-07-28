#!/bin/bash

# AI Share Platform - Proxy Service Stop Script
# This script stops only the proxy services

echo "🛑 Stopping AI Share Platform Proxy Services..."

# Function to stop process by PID file
stop_by_pid_file() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo "🔄 Stopping $service_name (PID: $pid)..."
            kill -TERM $pid 2>/dev/null
            sleep 2
            
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                echo "🔄 Force stopping $service_name (PID: $pid)..."
                kill -9 $pid 2>/dev/null
            fi
            
            echo "✅ $service_name stopped"
        else
            echo "⚠️  $service_name PID file exists but process not running"
        fi
        rm -f "$pid_file"
    fi
}

# Function to stop process on a specific port
stop_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null)
    
    if [ ! -z "$pids" ]; then
        echo "🔄 Stopping processes on port $port..."
        for pid in $pids; do
            kill -TERM $pid 2>/dev/null
            sleep 1
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                kill -9 $pid 2>/dev/null
            fi
        done
        echo "✅ Port $port cleared"
    fi
}

# Stop proxy service using PID file
stop_by_pid_file "proxy_service.pid" "Proxy Service"

# Stop processes on proxy ports as backup
echo "🧹 Cleaning up proxy ports..."
for port in 10101 10102 10103 10104 10105 10106 10107; do
    stop_port $port
done

# Wait for processes to stop
sleep 2

# Verify all proxy ports are free
echo ""
echo "🔍 Verifying proxy ports are free..."
all_stopped=true

for port in 10101 10102 10103 10104 10105 10106 10107; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Port $port: Still in use"
        all_stopped=false
    else
        echo "✅ Port $port: Free"
    fi
done

echo ""
if [ "$all_stopped" = true ]; then
    echo "🎉 All proxy services stopped successfully!"
else
    echo "⚠️  Some ports may still be in use. You may need to manually kill remaining processes."
    echo "   Use: lsof -ti:PORT | xargs kill -9"
fi

echo ""
echo "📋 Log files preserved at:"
echo "  - Proxy Service: logs/proxy_service.log"
echo ""
echo "🚀 To restart proxy services:"
echo "  ./start-proxy.sh"