#!/bin/bash
# Security patches update script
# This script updates only the vulnerable packages to avoid dependency conflicts

echo "=== Updating Backend Security Patches ==="
echo "Note: Run this in the aishare-platform conda environment"
echo ""

# Update critical security fixes
echo "1. Updating PyMySQL (SQL injection fix)..."
pip install "pymysql==1.1.1" --upgrade

echo "2. Updating snowflake-connector-python (multiple CVE fixes)..."
pip install "snowflake-connector-python==3.12.3" --upgrade

echo "3. Updating redshift-connector (OAuth2 issue fix)..."
pip install "redshift-connector==2.1.3" --upgrade

echo ""
echo "=== Backend updates complete ==="
echo ""
echo "For Starlette and requests vulnerabilities, consider these notes:"
echo "- Starlette: Current version 0.46.2 is recent. Check if newer patches are available."
echo "- requests: Version 2.32.3 is recent. Update to 2.32.4 if available without conflicts."
echo ""
echo "=== Frontend Updates ==="
echo "Run in the frontend directory:"
echo "npm install axios@1.7.9"
echo "npm install next@15.3.6 eslint-config-next@15.3.6"
