#!/bin/bash

# Start MindsDB Server with Warning Suppression
echo "🚀 Starting MindsDB server..."

# Activate MindsDB environment
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate mindsdb-server

# Set environment variables to suppress warnings
export PYTHONWARNINGS="ignore::UserWarning:pydantic.*,ignore::UserWarning"
export MINDSDB_CONFIG_PATH="/Users/syaikhipin/Documents/program/simpleaisharing/mindsdb_config.json"

# Change to project directory
cd /Users/syaikhipin/Documents/program/simpleaisharing

# Start MindsDB with suppressed output for warnings
python -m mindsdb --config="$MINDSDB_CONFIG_PATH" 2>/dev/null &
MINDSDB_PID=$!

echo "✅ MindsDB server started with PID $MINDSDB_PID"
echo "📊 GUI available at http://127.0.0.1:47334/"
echo "🔧 To stop: kill $MINDSDB_PID"

# Save PID for later reference
echo $MINDSDB_PID > /tmp/mindsdb.pid