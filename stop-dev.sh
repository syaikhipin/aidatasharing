#!/bin/bash
# AI Share Platform - Stop Development Environment

echo "🛑 Stopping AI Share Platform..."

# Kill MindsDB processes
echo "🧠 Stopping MindsDB server..."
pkill -f "mindsdb.*--api.*http" 2>/dev/null
pkill -f "mindsdb.*--port.*47334" 2>/dev/null
pkill -f "mindsdb" 2>/dev/null

# Kill backend processes
echo "🔧 Stopping backend server..."
pkill -f "python.*start.py" 2>/dev/null
pkill -f "uvicorn.*main:app" 2>/dev/null

# Kill frontend processes  
echo "🎨 Stopping frontend server..."
pkill -f "npm.*run.*dev" 2>/dev/null
pkill -f "next.*dev" 2>/dev/null

# Wait a moment for processes to terminate
sleep 2

# Check if any processes are still running
if pgrep -f "mindsdb" > /dev/null; then
    echo "⚠️  Force killing remaining MindsDB processes..."
    pkill -9 -f "mindsdb" 2>/dev/null
fi

if pgrep -f "python.*start.py\|uvicorn.*main:app" > /dev/null; then
    echo "⚠️  Force killing remaining backend processes..."
    pkill -9 -f "python.*start.py" 2>/dev/null
    pkill -9 -f "uvicorn.*main:app" 2>/dev/null
fi

if pgrep -f "npm.*run.*dev\|next.*dev" > /dev/null; then
    echo "⚠️  Force killing remaining frontend processes..."
    pkill -9 -f "npm.*run.*dev" 2>/dev/null
    pkill -9 -f "next.*dev" 2>/dev/null
fi

echo "✅ All services stopped"
