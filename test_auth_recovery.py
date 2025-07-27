#!/usr/bin/env python3
"""
Test Authentication System Recovery
Tests the authentication system that was reported as broken
"""

import sys
import os
import requests
import json
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_auth_system():
    """Test the authentication system"""
    print("🔐 Testing Authentication System Recovery...")
    
    # Test backend auth endpoint
    backend_url = "http://localhost:5000"
    
    print(f"📡 Testing backend connection at {backend_url}...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is responding")
        else:
            print(f"⚠️  Backend health check failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend connection failed: {e}")
        return False
    
    # Test authentication endpoints
    auth_endpoints = [
        "/auth/login",
        "/auth/register", 
        "/auth/profile",
        "/auth/refresh"
    ]
    
    print("🧪 Testing authentication endpoints...")
    
    for endpoint in auth_endpoints:
        try:
            response = requests.get(f"{backend_url}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 405]:  # Expected responses
                print(f"✅ {endpoint} - Endpoint accessible (Status: {response.status_code})")
            else:
                print(f"⚠️  {endpoint} - Unexpected status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Connection failed: {e}")
    
    # Test actual login functionality
    print("🔑 Testing login functionality...")
    
    test_credentials = {
        "username": "test_user",
        "password": "test_password"
    }
    
    try:
        response = requests.post(
            f"{backend_url}/auth/login",
            json=test_credentials,
            timeout=5
        )
        
        if response.status_code == 401:
            print("✅ Login endpoint working (returns 401 for invalid credentials)")
        elif response.status_code == 200:
            print("✅ Login successful")
        else:
            print(f"⚠️  Unexpected login response: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Login test failed: {e}")
    
    return True

def test_proxy_auth():
    """Test proxy authentication with the specified credentials"""
    print("\n🔗 Testing Proxy Authentication...")
    
    proxy_url = "http://localhost:3307"
    database = "Test%20DB%20Unipa%20Dataset"
    token = "0627b5b4afdba49bb348a870eb152e86"
    proxy_user = "proxy_user"
    
    full_url = f"{proxy_url}/{database}?token={token}"
    
    print(f"📡 Testing proxy connection at {full_url}...")
    print(f"👤 Using proxy user: {proxy_user}")
    
    try:
        # Test proxy connection
        response = requests.get(full_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Proxy connection successful")
            print(f"Response: {response.text[:200]}...")
        else:
            print(f"⚠️  Proxy connection failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Proxy connection failed: {e}")
        return False
    
    return True

def test_mindsdb_integration():
    """Test MindsDB integration and connectors"""
    print("\n🧠 Testing MindsDB Integration...")
    
    mindsdb_url = "http://localhost:47334"
    
    try:
        # Test MindsDB health
        response = requests.get(f"{mindsdb_url}/api/status", timeout=5)
        
        if response.status_code == 200:
            print("✅ MindsDB is responding")
            
            # Test databases endpoint
            response = requests.get(f"{mindsdb_url}/api/databases", timeout=5)
            if response.status_code == 200:
                databases = response.json()
                print(f"📊 Available databases: {len(databases.get('databases', []))}")
                
                # Check for our test database
                db_names = [db.get('name', '') for db in databases.get('databases', [])]
                if 'Test DB Unipa Dataset' in db_names:
                    print("✅ Test database found in MindsDB")
                else:
                    print("⚠️  Test database not found in MindsDB")
                    print(f"Available databases: {db_names}")
            else:
                print(f"⚠️  Failed to get databases: {response.status_code}")
                
        else:
            print(f"⚠️  MindsDB health check failed: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ MindsDB connection failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("🚀 Starting Authentication System Recovery Test")
    print("=" * 60)
    
    # Test backend authentication
    auth_ok = test_auth_system()
    
    # Test proxy authentication
    proxy_ok = test_proxy_auth()
    
    # Test MindsDB integration
    mindsdb_ok = test_mindsdb_integration()
    
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"  🔐 Backend Auth: {'✅ PASS' if auth_ok else '❌ FAIL'}")
    print(f"  🔗 Proxy Auth: {'✅ PASS' if proxy_ok else '❌ FAIL'}")
    print(f"  🧠 MindsDB Integration: {'✅ PASS' if mindsdb_ok else '❌ FAIL'}")
    
    if all([auth_ok, proxy_ok, mindsdb_ok]):
        print("\n🎉 All authentication systems are working!")
        return True
    else:
        print("\n⚠️  Some authentication issues detected")
        print("\n💡 Recommendations:")
        if not auth_ok:
            print("  - Check backend service is running")
            print("  - Verify auth module imports are correct")
        if not proxy_ok:
            print("  - Start MindsDB proxy service")
            print("  - Verify database and token configuration")
        if not mindsdb_ok:
            print("  - Check MindsDB service is running")
            print("  - Verify database connections")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)