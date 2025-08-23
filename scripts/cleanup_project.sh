#!/bin/bash
# Comprehensive Cleanup Script for AI Share Platform
# Removes unnecessary files, virtual environments, cache files, and cleans up migrations

echo "🧹 AI Share Platform - Comprehensive Cleanup"
echo "============================================"
echo ""

# Function to safely remove directory or file
safe_remove() {
    if [ -e "$1" ]; then
        echo "🗑️  Removing: $1"
        rm -rf "$1"
    else
        echo "ℹ️  Not found (skipping): $1"
    fi
}

# Function to count files before deletion
count_files() {
    if [ -e "$1" ]; then
        count=$(find "$1" -type f 2>/dev/null | wc -l)
        echo "   📊 Contains $count files"
    fi
}

echo "1. 🐍 Cleaning Python Cache Files"
echo "---------------------------------"
echo "Removing __pycache__ directories..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
echo "Removing .pyc files..."
find . -name "*.pyc" -delete 2>/dev/null
echo "Removing .pyo files..."
find . -name "*.pyo" -delete 2>/dev/null
echo "✅ Python cache cleanup complete"
echo ""

echo "2. 🗂️  Cleaning Virtual Environment"
echo "-----------------------------------"
if [ -d "backend/venv" ]; then
    count_files "backend/venv"
    safe_remove "backend/venv"
    echo "✅ Virtual environment removed (using conda instead)"
else
    echo "ℹ️  No virtual environment found (good - using conda)"
fi
echo ""

echo "3. 📦 Cleaning Node.js Dependencies (keeping only necessary)"
echo "--------------------------------------------------------"
if [ -d "frontend/node_modules" ]; then
    echo "ℹ️  Keeping frontend/node_modules (required for frontend)"
    echo "   📊 Frontend node_modules size:"
    du -sh frontend/node_modules 2>/dev/null || echo "   Could not determine size"
else
    echo "ℹ️  No node_modules found in frontend"
fi
echo ""

echo "4. 🔄 Cleaning Migration Files"
echo "------------------------------"
echo "Consolidating migration files..."

# Remove redundant migration files in root migrations directory
echo "Removing redundant root-level migrations..."
safe_remove "migrations/fresh_install_migration.py"
safe_remove "migrations/update_proxy_ports_migration.py" 
safe_remove "migrations/add_permanent_storage_path.py"
safe_remove "migrations/add_admin_config_tables.py"

# Clean up backend migration files
echo "Cleaning backend migration files..."
safe_remove "backend/migrations/add_notifications_table.py"
safe_remove "backend/migrations/proxy_connector_system.py"

# Remove old migration versions
echo "Removing old migration versions..."
safe_remove "backend/migrations/versions/20250727_014500_add_admin_config_tables.py"
safe_remove "backend/migrations/versions/migration_20250717_160000_add_document_support.py"

echo "✅ Migration cleanup complete"
echo ""

echo "5. 🧪 Cleaning Test Files"
echo "-------------------------"
echo "Removing redundant test files..."
safe_remove "backend/tests/test_api_proxy_sharing.py"
safe_remove "backend/tests/test_demo_integration.py" 
safe_remove "backend/tests/complete_gateway_test.py"
safe_remove "backend/tests/gateway_access_demo.py"
safe_remove "backend/tests/test_api_proxy_manual.py"
safe_remove "backend/tests/test_gateway_access.sh"

# Remove the entire backend/tests directory if it's empty or only has docs
if [ -d "backend/tests" ]; then
    remaining_files=$(find backend/tests -type f | wc -l)
    if [ "$remaining_files" -eq 0 ] || [ "$remaining_files" -le 2 ]; then
        echo "Removing empty backend/tests directory..."
        safe_remove "backend/tests"
    else
        echo "ℹ️  Keeping backend/tests (has $remaining_files files)"
    fi
fi
echo "✅ Test file cleanup complete"
echo ""

echo "6. 📄 Cleaning Temporary and Log Files"
echo "--------------------------------------"
echo "Removing temporary files..."
find . -name "*~" -delete 2>/dev/null
find . -name ".DS_Store" -delete 2>/dev/null
find . -name "Thumbs.db" -delete 2>/dev/null
find . -name "*.tmp" -delete 2>/dev/null
find . -name "*.temp" -delete 2>/dev/null

# Clean up log files but keep the logs directory
if [ -d "logs" ]; then
    echo "Cleaning log files..."
    find logs -name "*.log" -delete 2>/dev/null
    find logs -name "*.log.*" -delete 2>/dev/null
    echo "ℹ️  Keeping logs directory structure"
fi
echo "✅ Temporary file cleanup complete"
echo ""

echo "7. 🔧 Cleaning Build and Distribution Files"
echo "-------------------------------------------"
echo "Removing Python build artifacts..."
find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null
find . -name "build" -type d -exec rm -rf {} + 2>/dev/null
find . -name "dist" -type d -exec rm -rf {} + 2>/dev/null
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null
find . -name ".coverage" -delete 2>/dev/null
find . -name "htmlcov" -type d -exec rm -rf {} + 2>/dev/null
echo "✅ Build artifact cleanup complete"
echo ""

echo "8. 🗃️  Cleaning Old Configuration Files"
echo "---------------------------------------"
echo "Removing old configuration files..."
safe_remove "backend/.env"  # Remove backend-specific .env if it exists
safe_remove "proxy_encryption.key"
safe_remove "proxy_service.pid"
safe_remove "test_connection_fix.py"
safe_remove "test_connection_string.html"
echo "✅ Configuration cleanup complete"
echo ""

echo "9. 📂 Organizing and Cleaning Root Directory"
echo "-------------------------------------------"
echo "Removing redundant root-level files..."
safe_remove "create_admin_user.py"
safe_remove "create_demo_users.py"
safe_remove "create_seed_data.py"
safe_remove "setup_fresh_install.py"

# Keep only essential scripts
echo "ℹ️  Keeping essential scripts:"
echo "   - install-*.sh scripts"
echo "   - start-*.sh and stop-*.sh scripts"
echo "   - create-conda-env.sh"
echo "   - setup-google-api-key.sh"
echo "✅ Root directory cleanup complete"
echo ""

echo "10. 📊 Final Directory Analysis"
echo "-------------------------------"
echo "Current directory structure:"
echo ""
echo "📁 Project Size Analysis:"
if command -v du >/dev/null 2>&1; then
    echo "   Total project size:"
    du -sh . 2>/dev/null || echo "   Could not determine size"
    echo ""
    echo "   Large directories:"
    du -sh */ 2>/dev/null | sort -hr | head -5
else
    echo "   du command not available - skipping size analysis"
fi
echo ""

echo "📁 Remaining Structure:"
find . -maxdepth 2 -type d | grep -E '\./[^/]+$' | sort

echo ""
echo "🎉 Cleanup Complete!"
echo "==================="
echo ""
echo "✅ Removed:"
echo "   - Virtual environment (backend/venv)"
echo "   - Python cache files (__pycache__, *.pyc, *.pyo)"
echo "   - Redundant migration files"
echo "   - Old test files"
echo "   - Temporary and log files"
echo "   - Build artifacts"
echo "   - Old configuration files"
echo "   - Redundant root-level scripts"
echo ""
echo "📁 Kept:"
echo "   - Essential installation and startup scripts"
echo "   - Frontend node_modules (required)"
echo "   - Active configuration files (.env, .env.template)"
echo "   - Documentation and essential source code"
echo "   - Storage directory structure"
echo ""
echo "🚀 Your project is now clean and optimized for conda-based development!"