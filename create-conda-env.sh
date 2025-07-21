#!/bin/bash

# AI Share Platform - Conda Environment Creation Script
# This script creates the aishare-platform conda environment with Python 3.12

set -e  # Exit on any error

echo "🐍 Creating AI Share Platform Conda Environment..."
echo "================================================"

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "❌ Conda is not installed or not in PATH."
    echo "   Please install Anaconda or Miniconda first:"
    echo "   https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo "✅ Conda found: $(conda --version)"

# Check if environment already exists
if conda info --envs | grep -q "aishare-platform"; then
    echo "⚠️  Conda environment 'aishare-platform' already exists."
    read -p "Do you want to remove and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing existing environment..."
        conda env remove -n aishare-platform -y
        echo "✅ Existing environment removed"
    else
        echo "✅ Using existing environment"
        echo "   To activate: conda activate aishare-platform"
        exit 0
    fi
fi

# Create new environment
echo "🔨 Creating conda environment 'aishare-platform' with Python 3.10..."
conda create -n aishare-platform python=3.10 -y

if [ $? -eq 0 ]; then
    echo "✅ Conda environment 'aishare-platform' created successfully!"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Activate the environment: conda activate aishare-platform"
    echo "   2. Install dependencies: ./install-deps.sh"
    echo "   3. Start development: ./start-dev.sh"
    echo ""
else
    echo "❌ Failed to create conda environment"
    exit 1
fi