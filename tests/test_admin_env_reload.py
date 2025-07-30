#!/usr/bin/env python3
"""
Test script to verify admin environment variable reload functionality
and login page demo users functionality.
"""

import requests
import json
import sys
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
REQUEST_TIMEOUT = 10  # 10 seconds timeout

def create_session():
    """Create a requests session with timeout and retry strategy"""
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def check_backend_health():
    """Check if backend is running"""
    print("🏥 Checking backend health...")
    
    try:
        session = create_session()
        response = session.get(f"{BACKEND_URL}/docs", timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectTimeout:
        print("❌ Backend connection timeout - is the backend running on port 8000?")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend - is the backend running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ Backend health check error: {e}")
        return False

def check_frontend_health():
    """Check if frontend is running"""
    print("🌐 Checking frontend health...")
    
    try:
        session = create_session()
        response = session.get(FRONTEND_URL, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            print("✅ Frontend is running")
            return True
        else:
            print(f"❌ Frontend health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectTimeout:
        print("❌ Frontend connection timeout - is the frontend running on port 3000?")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to frontend - is the frontend running on port 3000?")
        return False
    except Exception as e:
        print(f"❌ Frontend health check error: {e}")
        return False

def test_demo_users_endpoint():
    """Test the demo users endpoint"""
    print("🧪 Testing demo users endpoint...")
    
    try:
        session = create_session()
        response = session.get(f"{BACKEND_URL}/api/auth/demo-users", timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Demo users endpoint working")
            print(f"   Found {data.get('total_count', 0)} demo users")
            
            for user in data.get('demo_users', []):
                print(f"   - {user['email']} ({user['description']})")
            
            return True
        else:
            print(f"❌ Demo users endpoint failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Demo users endpoint timeout")
        return False
    except Exception as e:
        print(f"❌ Error testing demo users endpoint: {e}")
        return False

def test_admin_login():
    """Test admin login and get token"""
    print("🔐 Testing admin login...")
    
    try:
        session = create_session()
        
        # Login as admin
        login_data = {
            'username': 'admin@example.com',
            'password': 'admin123'
        }
        
        response = session.post(
            f"{BACKEND_URL}/api/auth/login",
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            print(f"✅ Admin login successful")
            return access_token
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Admin login timeout")
        return None
    except Exception as e:
        print(f"❌ Error testing admin login: {e}")
        return None

def test_environment_reload(access_token):
    """Test environment variables reload endpoint"""
    print("🔄 Testing environment variables reload...")
    
    try:
        session = create_session()
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = session.post(
            f"{BACKEND_URL}/api/admin/environment/environment-variables/reload",
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Environment reload successful")
            print(f"   Reloaded {data.get('total_variables_reloaded', 0)} variables")
            
            # Show file results
            file_results = data.get('file_results', {})
            for file_path, result in file_results.items():
                status = result.get('status', 'unknown')
                if status == 'success':
                    count = result.get('variables_count', 0)
                    print(f"   - {file_path}: {count} variables")
                elif status == 'not_found':
                    print(f"   - {file_path}: file not found")
                else:
                    print(f"   - {file_path}: {status}")
            
            return True
        else:
            print(f"❌ Environment reload failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Environment reload timeout")
        return False
    except Exception as e:
        print(f"❌ Error testing environment reload: {e}")
        return False

def test_environment_variables_endpoint(access_token):
    """Test getting environment variables"""
    print("📋 Testing environment variables endpoint...")
    
    try:
        session = create_session()
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = session.get(
            f"{BACKEND_URL}/api/admin/environment/environment-variables",
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Environment variables endpoint working")
            print(f"   Total variables: {data.get('total_variables', 0)}")
            
            # Show categories
            categories = data.get('categories', {})
            for category, vars_dict in categories.items():
                if vars_dict:
                    print(f"   - {category}: {len(vars_dict)} variables")
            
            return True
        else:
            print(f"❌ Environment variables endpoint failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Environment variables endpoint timeout")
        return False
    except Exception as e:
        print(f"❌ Error testing environment variables endpoint: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Admin Environment Reload and Demo Users Functionality")
    print("=" * 70)
    
    # First check if services are running
    backend_ok = check_backend_health()
    frontend_ok = check_frontend_health()
    
    if not backend_ok:
        print("\n❌ Backend is not accessible. Please start the backend service first.")
        print("   Run: cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return 1
    
    if not frontend_ok:
        print("\n⚠️  Frontend is not accessible. Some tests will be skipped.")
        print("   Run: cd frontend && npm run dev")
    
    print("\n" + "=" * 70)
    
    results = []
    
    # Test demo users endpoint
    results.append(test_demo_users_endpoint())
    
    # Test admin login
    access_token = test_admin_login()
    if access_token:
        results.append(True)
        
        # Test environment variables endpoints
        results.append(test_environment_variables_endpoint(access_token))
        results.append(test_environment_reload(access_token))
    else:
        results.extend([False, False])
    
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    
    test_names = [
        "Demo Users Endpoint",
        "Admin Login",
        "Environment Variables Endpoint", 
        "Environment Reload Endpoint"
    ]
    
    passed = 0
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {i+1}. {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The functionality is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())