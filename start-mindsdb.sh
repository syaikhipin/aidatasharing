#!/bin/bash

# Start MindsDB Server with Warning Suppression
echo "🚀 Starting MindsDB server..."

# Activate MindsDB environment
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate mindsdb-server

# Set environment variables to suppress warnings
export PYTHONWARNINGS="ignore::UserWarning"
export PYDANTIC_DISABLE_PROTECTED_NAMESPACES="1"
export MINDSDB_CONFIG_PATH="/Users/syaikhipin/Documents/program/simpleaisharing/mindsdb_config.json"

# Change to project directory
cd /Users/syaikhipin/Documents/program/simpleaisharing

# Start MindsDB with suppressed output for warnings and run in background
nohup python -m mindsdb --config="$MINDSDB_CONFIG_PATH" > /dev/null 2>&1 &
MINDSDB_PID=$!

# Wait a moment for startup
sleep 3

# Check if the process is still running
if kill -0 $MINDSDB_PID 2>/dev/null; then
    echo "✅ MindsDB server started with PID $MINDSDB_PID"
    echo "📊 GUI available at http://127.0.0.1:47334/"
    echo "🔧 To stop: kill $MINDSDB_PID"
    
    # Save PID for later reference
    echo $MINDSDB_PID > /tmp/mindsdb.pid
else
    echo "❌ MindsDB failed to start. Check the logs for details."
    exit 1
fi