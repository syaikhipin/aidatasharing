#!/bin/bash
# Configuration Cleanup Test Suite
# Tests all aspects of the new configuration management system

echo "🧪 AI Share Platform - Configuration Cleanup Test Suite"
echo "======================================================"
echo ""

# Test 1: Configuration Validation
echo "📋 Test 1: Configuration Validation"
echo "-----------------------------------"
cd backend
if python config_cli.py validate; then
    echo "✅ Configuration validation: PASSED"
else
    echo "❌ Configuration validation: FAILED"
    exit 1
fi
echo ""

# Test 2: Configuration Display
echo "📋 Test 2: Configuration Summary"
echo "--------------------------------"
if python config_cli.py show > /dev/null; then
    echo "✅ Configuration summary: PASSED"
else
    echo "❌ Configuration summary: FAILED"
    exit 1
fi
echo ""

# Test 3: Environment Loading
echo "📋 Test 3: Environment Variable Loading"
echo "---------------------------------------"
JWT_KEY=$(python -c "
from dotenv import load_dotenv
import os
load_dotenv('../.env')
print(len(os.getenv('JWT_SECRET_KEY', '')))
")

if [ "$JWT_KEY" -gt 30 ]; then
    echo "✅ Environment loading: PASSED (JWT_SECRET_KEY: $JWT_KEY chars)"
else
    echo "❌ Environment loading: FAILED (JWT_SECRET_KEY: $JWT_KEY chars)"
    exit 1
fi
echo ""

# Test 4: Port Configuration
echo "📋 Test 4: Port Configuration"
echo "-----------------------------"
PORTS=$(python -c "
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('../.env')
from app.core.app_config import get_app_config
config = get_app_config()
ports = config.get_all_ports()
print(len(ports))
")

if [ "$PORTS" -eq 10 ]; then
    echo "✅ Port configuration: PASSED ($PORTS ports configured)"
else
    echo "❌ Port configuration: FAILED ($PORTS ports configured, expected 10)"
    exit 1
fi
echo ""

# Test 5: Proxy Configuration
echo "📋 Test 5: Proxy Configuration" 
echo "------------------------------"
PROXY_PORTS=$(python -c "
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('../.env')
from app.core.app_config import get_app_config
config = get_app_config()
proxy_ports = config.proxy.get_proxy_ports()
print(len(proxy_ports))
")

if [ "$PROXY_PORTS" -eq 7 ]; then
    echo "✅ Proxy configuration: PASSED ($PROXY_PORTS proxy services configured)"
else
    echo "❌ Proxy configuration: FAILED ($PROXY_PORTS proxy services, expected 7)"
    exit 1
fi
echo ""

# Test 6: Configuration Templates
echo "📋 Test 6: Configuration Templates"
echo "----------------------------------"
if [ -f "../.env.template" ] && [ -f "../frontend/.env.local" ]; then
    echo "✅ Configuration templates: PASSED"
else
    echo "❌ Configuration templates: FAILED"
    echo "   Missing files:"
    [ ! -f "../.env.template" ] && echo "   - .env.template"
    [ ! -f "../frontend/.env.local" ] && echo "   - frontend/.env.local"
    exit 1
fi
echo ""

# Test 7: Documentation
echo "📋 Test 7: Documentation"
echo "------------------------"
if [ -f "../docs/CONFIGURATION_CLEANUP_COMPLETE.md" ]; then
    echo "✅ Documentation: PASSED"
else
    echo "❌ Documentation: FAILED (missing CONFIGURATION_CLEANUP_COMPLETE.md)"
    exit 1
fi
echo ""

cd ..

echo "🎉 All Configuration Tests PASSED!"
echo "=================================="
echo ""
echo "📊 Test Summary:"
echo "  ✅ Configuration validation system working"
echo "  ✅ Environment variable loading working"
echo "  ✅ Port configuration system working"
echo "  ✅ Proxy configuration system working"  
echo "  ✅ Configuration templates available"
echo "  ✅ Documentation complete"
echo ""
echo "🚀 The configuration cleanup is complete and all systems are operational!"
echo ""
echo "📚 Next Steps:"
echo "  1. Review configuration settings in .env file"
echo "  2. Update API keys and secrets for your environment"
echo "  3. Run 'cd backend && python config_cli.py validate' before starting services"
echo "  4. Read docs/CONFIGURATION_CLEANUP_COMPLETE.md for detailed information"
echo ""