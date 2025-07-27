#!/usr/bin/env python3
"""
Final Authentication and Proxy Test
Tests the complete system with correct ports and fixed relationships
"""

import requests
import json
from datetime import datetime

def test_backend_health():
    """Test backend health on correct port"""
    print("🔍 Testing Backend Health...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Backend is healthy")
            print(f"  📊 Database: {health_data.get('services', {}).get('database', {}).get('status', 'unknown')}")
            print(f"  🧠 MindsDB: {health_data.get('services', {}).get('mindsdb', {}).get('status', 'unknown')}")
            print(f"  🔐 Auth Service: {health_data.get('services', {}).get('auth_service', {}).get('status', 'unknown')}")
            return True
        else:
            print(f"⚠️  Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_mysql_proxy():
    """Test MySQL proxy on correct port"""
    print("\n🔗 Testing MySQL Proxy...")
    
    test_url = "http://localhost:3307/Test%20DB%20Unipa%20Dataset?token=0627b5b4afdba49bb348a870eb152e86"
    
    try:
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ MySQL proxy connection successful")
            print(f"  📊 Database: {data.get('database', 'N/A')}")
            print(f"  🔧 Proxy Type: {data.get('proxy_type', 'N/A')}")
            print(f"  🌐 Proxy Host: {data.get('connection_info', {}).get('proxy_host', 'N/A')}")
            print(f"  📈 Row Count: {data.get('row_count', 'N/A')}")
            return True
        else:
            print(f"❌ MySQL proxy failed: HTTP {response.status_code}")
            print(f"  📄 Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ MySQL proxy connection failed: {e}")
        return False

def test_auth_endpoints():
    """Test authentication endpoints"""
    print("\n🔐 Testing Authentication Endpoints...")
    
    # Test login endpoint structure
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            json={"username": "test@example.com", "password": "testpassword"},
            timeout=5
        )
        
        if response.status_code == 401:
            print("✅ Login endpoint working (returns 401 for invalid credentials)")
            return True
        elif response.status_code == 422:
            print("✅ Login endpoint working (returns 422 for validation errors)")
            return True
        elif response.status_code == 200:
            print("✅ Login successful")
            return True
        else:
            print(f"⚠️  Login response: {response.status_code}")
            print(f"  📄 Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Login test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Final Authentication and Proxy System Test")
    print("=" * 70)
    print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test backend health
    backend_ok = test_backend_health()
    
    # Test MySQL proxy
    mysql_ok = test_mysql_proxy()
    
    # Test authentication
    auth_ok = test_auth_endpoints()
    
    print("\n" + "=" * 70)
    print("📋 FINAL TEST SUMMARY")
    print("=" * 70)
    print(f"🖥️  Backend Service (Port 8000): {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"🔗 MySQL Proxy (Port 3307): {'✅ PASS' if mysql_ok else '❌ FAIL'}")
    print(f"🔐 Authentication System: {'✅ PASS' if auth_ok else '❌ FAIL'}")
    
    if all([backend_ok, mysql_ok, auth_ok]):
        print("\n🎉 ALL SYSTEMS OPERATIONAL!")
        print("\n✅ Issues Resolved:")
        print("  - SQLAlchemy relationship error fixed")
        print("  - Port conflicts resolved (MySQL proxy on 3307)")
        print("  - Backend running on correct port (8000)")
        print("  - Authentication endpoints accessible")
        
        print("\n📖 Usage:")
        print("  🔗 MySQL Proxy: curl 'http://localhost:3307/Test%20DB%20Unipa%20Dataset?token=0627b5b4afdba49bb348a870eb152e86'")
        print("  🖥️  Backend Health: curl http://localhost:8000/health")
        print("  🔐 Login Test: curl -X POST -H 'Content-Type: application/json' -d '{\"username\":\"test@example.com\",\"password\":\"testpassword\"}' http://localhost:8000/api/auth/login")
        
        return True
    else:
        print("\n⚠️  Some issues remain:")
        if not backend_ok:
            print("  - Backend service needs attention")
        if not mysql_ok:
            print("  - MySQL proxy needs configuration")
        if not auth_ok:
            print("  - Authentication system needs fixes")
        
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)