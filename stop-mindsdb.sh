#!/bin/bash

# Stop MindsDB Server
echo "🛑 Stopping MindsDB server..."

# Check if PID file exists
if [ -f /tmp/mindsdb.pid ]; then
    MINDSDB_PID=$(cat /tmp/mindsdb.pid)
    
    # Check if process is running
    if kill -0 $MINDSDB_PID 2>/dev/null; then
        echo "Found MindsDB process with PID $MINDSDB_PID, stopping..."
        kill $MINDSDB_PID
        
        # Wait for process to stop
        sleep 2
        
        # Check if process stopped
        if kill -0 $MINDSDB_PID 2>/dev/null; then
            echo "Process still running, forcing stop..."
            kill -9 $MINDSDB_PID
        fi
        
        echo "✅ MindsDB server stopped"
        rm /tmp/mindsdb.pid
    else
        echo "⚠️  MindsDB process not running"
        rm /tmp/mindsdb.pid
    fi
else
    # Try to find and kill any MindsDB processes
    PIDS=$(ps aux | grep "python -m mindsdb" | grep -v grep | awk '{print $2}')
    
    if [ -n "$PIDS" ]; then
        echo "Found MindsDB processes: $PIDS"
        echo $PIDS | xargs kill
        sleep 2
        
        # Force kill if still running
        REMAINING=$(ps aux | grep "python -m mindsdb" | grep -v grep | awk '{print $2}')
        if [ -n "$REMAINING" ]; then
            echo "Force killing remaining processes..."
            echo $REMAINING | xargs kill -9
        fi
        
        echo "✅ MindsDB server stopped"
    else
        echo "⚠️  No MindsDB processes found"
    fi
fi