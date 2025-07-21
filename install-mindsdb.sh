#!/bin/bash

# AI Share Platform - MindsDB Installation Script
# This script handles MindsDB installation with dependency conflict resolution

set -e  # Exit on any error

echo "🧠 Installing MindsDB for AI Share Platform..."
echo "================================================"

# Activate conda environment
echo "📦 Activating conda environment: aishare-platform"
if conda info --envs | grep -q "aishare-platform"; then
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate aishare-platform
    echo "✅ Activated conda environment: aishare-platform"
else
    echo "❌ Conda environment 'aishare-platform' not found. Please create it first."
    echo "   Run: conda create -n aishare-platform python=3.9"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if MindsDB is already installed
if command_exists mindsdb; then
    echo "✅ MindsDB already installed: $(mindsdb --version 2>/dev/null || echo 'version check failed')"
    exit 0
fi

echo "📦 Installing MindsDB..."
echo "⚠️  Note: MindsDB has known dependency conflicts with some packages"
echo "   This is normal and the application should still work"
echo ""

# Method 1: Install MindsDB without dependencies to avoid conflicts
# Temporarily skip methods 1-3 for clean source install
# echo "🔄 Method 1: Installing MindsDB without dependencies"
if pip3 install mindsdb --no-deps 2>/dev/null; then
    echo "✅ MindsDB core installed without dependencies"
    
    # Install only essential dependencies that don't conflict
    echo "📦 Installing essential MindsDB dependencies..."
    pip3 install lightwood --no-warn-conflicts 2>/dev/null || true
    
    # Refresh shell environment
    hash -r 2>/dev/null || true
    
    if command_exists mindsdb; then
        echo "✅ MindsDB installed successfully without conflicts"
        exit 0
    fi
fi

# echo "⚠️  No-deps installation had issues, trying with minimal dependencies..."
# echo "🔄 Method 2: Installing with minimal dependencies"
if pip3 install mindsdb --no-warn-conflicts 2>/dev/null; then
    echo "✅ MindsDB installed with warnings (conflicts expected)"
    
    # Refresh shell environment
    hash -r 2>/dev/null || true
    
    if command_exists mindsdb; then
        echo "✅ MindsDB command verified despite conflicts"
        exit 0
    fi
fi

# echo "🔄 Method 3: Trying conda installation"
if conda install -c conda-forge mindsdb -y 2>/dev/null; then
    echo "✅ MindsDB installed via conda"
    if command_exists mindsdb; then
        echo "✅ MindsDB command verified"
        exit 0
    fi
fi

echo "🔄 Directly installing MindsDB from source for clean setup"
echo "📦 Creating separate conda environment for MindsDB server"
conda create -n mindsdb-server python=3.10 -y
conda activate mindsdb-server

echo "🔄 Installing MindsDB server from source in separate env"
if [ ! -d "mindsdb-source" ]; then
    git clone https://github.com/mindsdb/mindsdb.git mindsdb-source
fi
cd mindsdb-source
pip install -e .
pip install -r requirements/requirements-dev.txt
cd ..

# Start MindsDB server in background with proper configuration
echo "🚀 Starting MindsDB server with configuration"
export PYTHONWARNINGS="ignore::UserWarning:pydantic.*"
export MINDSDB_CONFIG_PATH="/Users/syaikhipin/Documents/program/simpleaisharing/mindsdb_config.json"
python -m mindsdb --config="$MINDSDB_CONFIG_PATH" > /dev/null 2>&1 &
MINDSDB_PID=$!
echo "MindsDB server running with PID $MINDSDB_PID"
# Wait a moment for server to start
sleep 3

# Switch back to main env
conda deactivate
conda activate aishare-platform

# Clean up any existing conflicting packages
echo "🧹 Cleaning up existing MindsDB packages in main env"
pip uninstall -y mindsdb mindsdb-sdk mindsdb-sql-parser mindsdb_sql mindsdb_sql_parser || true

# Install SDK in main env
echo "📦 Installing MindsDB SDK in main environment"
pip install mindsdb_sdk

if python -c "import mindsdb_sdk" 2>/dev/null; then
    echo "✅ MindsDB SDK installed successfully"
    echo "🎉 MindsDB setup complete with separate server environment"
    echo "To stop MindsDB server: kill $MINDSDB_PID"
    echo "The application can now use mindsdb_sdk to connect to localhost:47334"
    echo ""
    echo "🎉 MindsDB installation process completed!"
    echo "================================================"
    echo "You can now start the development environment with MindsDB support."
    echo ""
    exit 0
else
    echo "❌ Failed to install MindsDB SDK"
    echo ""
    echo "🔧 Manual installation options:"
    echo "   1. Separate conda environment:"
    echo "      conda create -n mindsdb-env python=3.10"
    echo "      conda activate mindsdb-env"
    echo "      pip install mindsdb"
    echo "   2. The application will work without MindsDB for basic functionality"
    echo "      (dataset upload, basic chat, etc.)"
    exit 1
fi

# Update final guidance to note separate env and how to stop server
echo "🎉 MindsDB setup complete with separate server environment"
echo "To stop MindsDB server: kill $MINDSDB_PID"
echo "The application can now use mindsdb_sdk to connect to localhost:47334"

if command_exists mindsdb; then
    echo "✅ MindsDB installed from source successfully"
    exit 0
fi

# Final check and guidance
echo "⚠️  MindsDB installation completed with potential conflicts"
echo "   Checking final status..."

# Force refresh the shell environment
hash -r 2>/dev/null || true

if command_exists mindsdb; then
    echo "✅ MindsDB command is available"
    echo "   Despite dependency conflicts, MindsDB should work for basic functionality"
    echo "   If you encounter issues, you may need to:"
    echo "   1. Use a separate conda environment for MindsDB"
    echo "   2. Use Docker for MindsDB (recommended for production)"
else
    echo "❌ MindsDB installation failed completely"
    echo ""
    echo "🔧 Manual installation options:"
    echo "   1. Docker (recommended):"
    echo "      docker run -p 47334:47334 mindsdb/mindsdb"
    echo ""
    echo "   2. Separate conda environment:"
    echo "      conda create -n mindsdb-env python=3.9"
    echo "      conda activate mindsdb-env"
    echo "      pip install mindsdb"
    echo ""
    echo "   3. The application will work without MindsDB for basic functionality"
    echo "      (dataset upload, basic chat, etc.)"
    exit 1
fi

echo ""
echo "🎉 MindsDB installation process completed!"
echo "================================================"
echo "You can now start the development environment with MindsDB support."
echo ""