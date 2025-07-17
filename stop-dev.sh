#!/bin/bash
# AI Share Platform - Stop Development Environment

echo "🛑 Stopping AI Share Platform..."

# Kill backend processes
pkill -f "python.*start.py" 2>/dev/null
pkill -f "uvicorn.*main:app" 2>/dev/null

# Kill frontend processes  
pkill -f "npm.*run.*dev" 2>/dev/null
pkill -f "next.*dev" 2>/dev/null

echo "✅ All services stopped"
