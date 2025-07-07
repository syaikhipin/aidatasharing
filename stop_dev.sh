#!/bin/bash

# AI Share Platform - Enhanced Development Environment Stop Script
# This script gracefully stops all development services with comprehensive logging

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"

# Logging function
log() {
    echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} ✅ $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} ⚠️ $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} ❌ $1"
}

# Function to check if a process is running
is_process_running() {
    local pid=$1
    if [ -z "$pid" ]; then
        return 1
    fi
    
    if ps -p "$pid" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to gracefully stop a process
stop_process() {
    local pid=$1
    local name=$2
    local timeout=${3:-10}
    
    if [ -z "$pid" ]; then
        log_warning "$name: No PID provided"
        return 1
    fi
    
    if ! is_process_running "$pid"; then
        log_warning "$name: Process $pid is not running"
        return 0
    fi
    
    log "Stopping $name (PID: $pid)..."
    
    # Send SIGTERM
    kill -TERM "$pid" 2>/dev/null || {
        log_warning "$name: Failed to send SIGTERM to PID $pid"
        return 1
    }
    
    # Wait for graceful shutdown
    local count=0
    while [ $count -lt $timeout ] && is_process_running "$pid"; do
        sleep 1
        count=$((count + 1))
        if [ $((count % 3)) -eq 0 ]; then
            log "$name: Waiting for graceful shutdown... ($count/${timeout}s)"
        fi
    done
    
    # Force kill if still running
    if is_process_running "$pid"; then
        log_warning "$name: Graceful shutdown timed out, force killing..."
        kill -KILL "$pid" 2>/dev/null || {
            log_error "$name: Failed to force kill PID $pid"
            return 1
        }
        sleep 2
        
        if is_process_running "$pid"; then
            log_error "$name: Process $pid still running after force kill"
            return 1
        else
            log_success "$name: Force killed successfully"
        fi
    else
        log_success "$name: Stopped gracefully"
    fi
    
    return 0
}

# Function to stop services by port
stop_service_by_port() {
    local port=$1
    local name=$2
    
    log "Checking for $name on port $port..."
    
    # Find process using the port
    local pid=$(lsof -ti:$port 2>/dev/null || true)
    
    if [ -z "$pid" ]; then
        log_warning "$name: No process found on port $port"
        return 0
    fi
    
    # Handle multiple PIDs
    for p in $pid; do
        local process_name=$(ps -p "$p" -o comm= 2>/dev/null || echo "unknown")
        log "Found $name process: $process_name (PID: $p)"
        stop_process "$p" "$name ($process_name)" 15
    done
    
    # Verify port is free
    if lsof -ti:$port >/dev/null 2>&1; then
        log_error "$name: Port $port is still in use after stopping processes"
        return 1
    else
        log_success "$name: Port $port is now free"
        return 0
    fi
}

# Function to stop MindsDB
stop_mindsdb() {
    log "🧠 Stopping MindsDB Server..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Check if MindsDB is running on port 47334
    if lsof -ti:47334 >/dev/null 2>&1; then
        stop_service_by_port 47334 "MindsDB"
    else
        log_warning "MindsDB: No process found on port 47334"
    fi
    
    # Also check for mindsdb processes by name
    local mindsdb_pids=$(pgrep -f "mindsdb" 2>/dev/null || true)
    if [ -n "$mindsdb_pids" ]; then
        for pid in $mindsdb_pids; do
            local cmd=$(ps -p "$pid" -o args= 2>/dev/null || echo "unknown")
            log "Found MindsDB process: $cmd (PID: $pid)"
            stop_process "$pid" "MindsDB" 15
        done
    fi
    
    log_success "MindsDB shutdown completed"
}

# Function to stop backend
stop_backend() {
    log "🔧 Stopping Backend (FastAPI)..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Stop backend on port 8000
    stop_service_by_port 8000 "Backend"
    
    # Check for uvicorn processes
    local uvicorn_pids=$(pgrep -f "uvicorn.*main:app" 2>/dev/null || true)
    if [ -n "$uvicorn_pids" ]; then
        for pid in $uvicorn_pids; do
            local cmd=$(ps -p "$pid" -o args= 2>/dev/null || echo "unknown")
            log "Found Uvicorn process: $cmd (PID: $pid)"
            stop_process "$pid" "Uvicorn" 10
        done
    fi
    
    log_success "Backend shutdown completed"
}

# Function to stop frontend
stop_frontend() {
    log "🌐 Stopping Frontend (Next.js)..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Stop frontend on port 3000
    stop_service_by_port 3000 "Frontend"
    
    # Check for next.js processes
    local nextjs_pids=$(pgrep -f "next.*dev" 2>/dev/null || true)
    if [ -n "$nextjs_pids" ]; then
        for pid in $nextjs_pids; do
            local cmd=$(ps -p "$pid" -o args= 2>/dev/null || echo "unknown")
            log "Found Next.js process: $cmd (PID: $pid)"
            stop_process "$pid" "Next.js" 10
        done
    fi
    
    # Check for npm/node processes in frontend directory
    local npm_pids=$(pgrep -f "npm.*run.*dev" 2>/dev/null || true)
    if [ -n "$npm_pids" ]; then
        for pid in $npm_pids; do
            local cmd=$(ps -p "$pid" -o args= 2>/dev/null || echo "unknown")
            if echo "$cmd" | grep -q "frontend"; then
                log "Found npm dev process: $cmd (PID: $pid)"
                stop_process "$pid" "npm dev" 10
            fi
        done
    fi
    
    log_success "Frontend shutdown completed"
}

# Function to clean up temporary files
cleanup_temp_files() {
    log "🧹 Cleaning up temporary files..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Clean up Python cache files
    if [ -d "$ROOT_DIR/backend" ]; then
        find "$ROOT_DIR/backend" -name "*.pyc" -delete 2>/dev/null || true
        find "$ROOT_DIR/backend" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
        log_success "Python cache files cleaned"
    fi
    
    # Clean up node temporary files
    if [ -d "$ROOT_DIR/frontend" ]; then
        if [ -d "$ROOT_DIR/frontend/.next" ]; then
            rm -rf "$ROOT_DIR/frontend/.next" 2>/dev/null || true
            log_success "Next.js cache cleaned"
        fi
    fi
    
    # Clean up log files (if any)
    if [ -d "$ROOT_DIR/logs" ]; then
        find "$ROOT_DIR/logs" -name "*.log" -mtime +7 -delete 2>/dev/null || true
        log_success "Old log files cleaned"
    fi
    
    log_success "Cleanup completed"
}

# Function to save shutdown report
save_shutdown_report() {
    local shutdown_time=$(date +'%Y-%m-%d %H:%M:%S')
    local report_file="$ROOT_DIR/logs/shutdown_report.log"
    
    # Create logs directory if it doesn't exist
    mkdir -p "$ROOT_DIR/logs"
    
    cat > "$report_file" << EOF
AI Share Platform - Shutdown Report
Generated: $shutdown_time

Services Stopped:
- MindsDB Server (Port 47334)
- Backend API (Port 8000)
- Frontend App (Port 3000)

Cleanup Actions:
- Python cache files removed
- Next.js cache cleared
- Temporary files cleaned

Shutdown Status: Completed Successfully
EOF
    
    log_success "Shutdown report saved to: $report_file"
}

# Function to check if any AI Share Platform processes are still running
final_check() {
    log "🔍 Performing final check for remaining processes..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    local remaining_processes=()
    
    # Check common ports
    for port in 47334 8000 3000; do
        if lsof -ti:$port >/dev/null 2>&1; then
            local pid=$(lsof -ti:$port)
            local process_name=$(ps -p "$pid" -o comm= 2>/dev/null || echo "unknown")
            remaining_processes+=("Port $port: $process_name (PID: $pid)")
        fi
    done
    
    # Check for specific process patterns
    local patterns=("mindsdb" "uvicorn.*main:app" "next.*dev" "npm.*run.*dev")
    for pattern in "${patterns[@]}"; do
        local pids=$(pgrep -f "$pattern" 2>/dev/null || true)
        if [ -n "$pids" ]; then
            for pid in $pids; do
                local cmd=$(ps -p "$pid" -o args= 2>/dev/null || echo "unknown")
                remaining_processes+=("$pattern: $cmd (PID: $pid)")
            done
        fi
    done
    
    if [ ${#remaining_processes[@]} -eq 0 ]; then
        log_success "No remaining AI Share Platform processes found"
        return 0
    else
        log_warning "Found ${#remaining_processes[@]} remaining process(es):"
        for process in "${remaining_processes[@]}"; do
            log_warning "  • $process"
        done
        
        echo ""
        read -p "Would you like to force kill these processes? (y/N): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log "Force killing remaining processes..."
            for port in 47334 8000 3000; do
                if lsof -ti:$port >/dev/null 2>&1; then
                    local pid=$(lsof -ti:$port)
                    kill -KILL "$pid" 2>/dev/null || true
                    log_success "Force killed process on port $port"
                fi
            done
        else
            log_warning "Remaining processes left running"
        fi
        
        return 1
    fi
}

# Main function
main() {
    echo ""
    echo "🛑━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━🛑"
    echo "🚀 AI SHARE PLATFORM - DEVELOPMENT ENVIRONMENT SHUTDOWN"
    echo "🛑━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━🛑"
    echo ""
    
    local start_time=$(date +%s)
    log "Starting graceful shutdown process..."
    echo ""
    
    # Check if we're in the right directory
    if [ ! -f "$ROOT_DIR/package.json" ] && [ ! -f "$ROOT_DIR/frontend/package.json" ]; then
        log_error "This doesn't appear to be the AI Share Platform root directory"
        log_error "Please run this script from the project root"
        exit 1
    fi
    
    # Stop services in reverse order (opposite of startup)
    stop_frontend
    echo ""
    
    stop_backend
    echo ""
    
    stop_mindsdb
    echo ""
    
    # Cleanup
    cleanup_temp_files
    echo ""
    
    # Final check
    final_check
    echo ""
    
    # Save report
    save_shutdown_report
    echo ""
    
    # Calculate shutdown duration
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo "🎯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━🎯"
    echo "🏁 AI SHARE PLATFORM - SHUTDOWN COMPLETED"
    echo "🎯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━🎯"
    echo ""
    log_success "All services have been stopped successfully!"
    log "Shutdown duration: ${duration} seconds"
    log "Timestamp: $(date +'%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "📋 WHAT WAS STOPPED:"
    echo "   🧠 MindsDB Server"
    echo "   🔧 Backend API (FastAPI)"
    echo "   🌐 Frontend App (Next.js)"
    echo "   🧹 Temporary files cleaned"
    echo ""
    echo "💡 TO RESTART:"
    echo "   Run: ./start-dev.sh"
    echo ""
    echo "🔧 TROUBLESHOOTING:"
    echo "   If issues persist:"
    echo "   • Check for remaining processes: ps aux | grep -E '(mindsdb|uvicorn|next)'"
    echo "   • Check port usage: lsof -i :47334 -i :8000 -i :3000"
    echo "   • Review logs in: ./logs/"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "👋 Thank you for using AI Share Platform!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Handle Ctrl+C gracefully
trap 'echo ""; log_warning "Shutdown interrupted by user"; exit 130' INT

# Handle other signals
trap 'echo ""; log_error "Shutdown terminated unexpectedly"; exit 1' TERM

# Run main function
main "$@" 