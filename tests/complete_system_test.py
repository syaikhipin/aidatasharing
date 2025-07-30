#!/usr/bin/env python3
"""
Complete System Test for AI Share Platform Demo Users
Tests the full integration between frontend, backend, and database.
"""

import requests
import json
import sys
from typing import List, Dict

# Configuration
FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"

def test_backend_demo_users():
    """Test backend demo-users endpoint directly"""
    print("🔍 Testing backend demo-users endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/auth/demo-users")
        if response.status_code == 200:
            data = response.json()
            users = data.get('demo_users', [])
            print(f"✅ Backend: Found {len(users)} demo users")
            for user in users:
                print(f"   - {user['email']} ({user['description']})")
            return users
        else:
            print(f"❌ Backend: Failed with status {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Backend: Error - {e}")
        return []

def test_frontend_proxy():
    """Test frontend proxy to backend"""
    print("\n🔍 Testing frontend proxy...")
    try:
        response = requests.get(f"{FRONTEND_URL}/api/auth/demo-users")
        if response.status_code == 200:
            data = response.json()
            users = data.get('demo_users', [])
            print(f"✅ Frontend Proxy: Found {len(users)} demo users")
            return users
        else:
            print(f"❌ Frontend Proxy: Failed with status {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Frontend Proxy: Error - {e}")
        return []

def test_login_functionality(users: List[Dict]):
    """Test login functionality for demo users"""
    print("\n🔍 Testing login functionality...")
    
    successful_logins = 0
    
    for user in users:
        email = user['email']
        password = user['password']
        
        try:
            # Test login via frontend proxy
            response = requests.post(
                f"{FRONTEND_URL}/api/auth/login",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=f"username={email}&password={password}"
            )
            
            if response.status_code == 200:
                token_data = response.json()
                if 'access_token' in token_data:
                    print(f"✅ Login successful: {email}")
                    successful_logins += 1
                else:
                    print(f"❌ Login failed: {email} - No access token")
            else:
                print(f"❌ Login failed: {email} - Status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Login error: {email} - {e}")
    
    print(f"\n📊 Login Results: {successful_logins}/{len(users)} successful")
    return successful_logins

def test_frontend_page():
    """Test if frontend login page loads"""
    print("\n🔍 Testing frontend login page...")
    try:
        response = requests.get(f"{FRONTEND_URL}/login")
        if response.status_code == 200:
            content = response.text
            if "Welcome Back" in content:
                print("✅ Frontend: Login page loads correctly")
                return True
            else:
                print("❌ Frontend: Login page content incorrect")
                return False
        else:
            print(f"❌ Frontend: Page failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend: Error - {e}")
        return False

def main():
    """Run complete system test"""
    print("🚀 AI Share Platform - Complete System Test")
    print("=" * 50)
    
    # Test 1: Backend demo users endpoint
    backend_users = test_backend_demo_users()
    
    # Test 2: Frontend proxy
    frontend_users = test_frontend_proxy()
    
    # Test 3: Login functionality
    if backend_users:
        successful_logins = test_login_functionality(backend_users)
    else:
        successful_logins = 0
    
    # Test 4: Frontend page
    frontend_page_ok = test_frontend_page()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SYSTEM TEST SUMMARY")
    print("=" * 50)
    
    backend_ok = len(backend_users) > 0
    proxy_ok = len(frontend_users) > 0
    login_ok = successful_logins > 0
    
    print(f"Backend Demo Users:     {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"Frontend Proxy:         {'✅ PASS' if proxy_ok else '❌ FAIL'}")
    print(f"Login Functionality:    {'✅ PASS' if login_ok else '❌ FAIL'}")
    print(f"Frontend Page:          {'✅ PASS' if frontend_page_ok else '❌ FAIL'}")
    
    all_tests_pass = backend_ok and proxy_ok and login_ok and frontend_page_ok
    
    print(f"\nOverall Status:         {'✅ ALL TESTS PASS' if all_tests_pass else '❌ SOME TESTS FAILED'}")
    
    if all_tests_pass:
        print("\n🎉 System is fully operational!")
        print("   - Backend API is running correctly")
        print("   - Frontend proxy is working")
        print("   - Demo users can login successfully")
        print("   - Frontend login page is accessible")
        print("\n🌐 Access the system at: http://localhost:3000/login")
    else:
        print("\n⚠️  System has issues that need attention.")
    
    return 0 if all_tests_pass else 1

if __name__ == "__main__":
    sys.exit(main())