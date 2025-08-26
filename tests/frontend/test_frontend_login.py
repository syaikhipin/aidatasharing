#!/usr/bin/env python3
"""
Test Frontend Login with Comprehensive Simulation Users
Tests that the frontend login page works with all the new simulation users.
"""

import requests
import json
import time

# Configuration
FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"

# Test users from comprehensive simulation
TEST_USERS = [
    # TechCorp Industries
    {"email": "alice.smith@techcorp.com", "password": "tech2024", "org": "TechCorp Industries"},
    {"email": "bob.johnson@techcorp.com", "password": "tech2024", "org": "TechCorp Industries"},
    {"email": "carol.williams@techcorp.com", "password": "tech2024", "org": "TechCorp Industries"},
    
    # DataScience Hub
    {"email": "david.brown@datasci.org", "password": "data2024", "org": "DataScience Hub"},
    {"email": "eva.davis@datasci.org", "password": "data2024", "org": "DataScience Hub"},
    {"email": "frank.miller@datasci.org", "password": "data2024", "org": "DataScience Hub"},
    
    # StartupLab
    {"email": "grace.wilson@startuplab.io", "password": "startup2024", "org": "StartupLab"},
    {"email": "henry.moore@startuplab.io", "password": "startup2024", "org": "StartupLab"},
    
    # Academic Research Institute
    {"email": "iris.taylor@research.edu", "password": "research2024", "org": "Academic Research Institute"},
    {"email": "jack.anderson@research.edu", "password": "research2024", "org": "Academic Research Institute"},
    
    # Demo Organization
    {"email": "demo1@demo.com", "password": "demo123", "org": "Demo Organization"},
    {"email": "demo2@demo.com", "password": "demo123", "org": "Demo Organization"},
]

def test_frontend_accessibility():
    """Test if frontend is accessible."""
    print("🌐 Testing Frontend Accessibility...")
    try:
        response = requests.get(f"{FRONTEND_URL}/login", timeout=10)
        if response.status_code == 200:
            print("✅ Frontend login page is accessible")
            return True
        else:
            print(f"❌ Frontend login page returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend accessibility test failed: {e}")
        return False

def test_backend_login(email, password):
    """Test backend login functionality."""
    try:
        data = {
            'username': email,
            'password': password
        }
        response = requests.post(f"{BACKEND_URL}/api/auth/login", data=data, timeout=10)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"Status {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_frontend_login_api(email, password):
    """Test frontend login API endpoint."""
    try:
        # Test through frontend proxy
        data = {
            'username': email,
            'password': password
        }
        response = requests.post(f"{FRONTEND_URL}/api/auth/login", data=data, timeout=10)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"Status {response.status_code}"
    except Exception as e:
        return False, str(e)

def main():
    """Main test function."""
    print("🚀 Testing Frontend Login with Comprehensive Simulation Users")
    print("=" * 70)
    
    # Test frontend accessibility
    if not test_frontend_accessibility():
        print("❌ Frontend is not accessible. Please start the frontend server.")
        return
    
    print(f"\n🧪 Testing {len(TEST_USERS)} simulation users...")
    
    backend_success = 0
    frontend_success = 0
    
    for i, user in enumerate(TEST_USERS, 1):
        print(f"\n{i:2d}. Testing {user['email']} ({user['org']})")
        
        # Test backend login
        backend_ok, backend_result = test_backend_login(user['email'], user['password'])
        if backend_ok:
            print(f"    ✅ Backend login successful")
            backend_success += 1
        else:
            print(f"    ❌ Backend login failed: {backend_result}")
        
        # Test frontend login API
        frontend_ok, frontend_result = test_frontend_login_api(user['email'], user['password'])
        if frontend_ok:
            print(f"    ✅ Frontend API login successful")
            frontend_success += 1
        else:
            print(f"    ❌ Frontend API login failed: {frontend_result}")
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.5)
    
    print(f"\n" + "=" * 70)
    print(f"📊 LOGIN TEST SUMMARY")
    print(f"=" * 70)
    print(f"Backend Login Success:  {backend_success}/{len(TEST_USERS)} ({backend_success/len(TEST_USERS)*100:.1f}%)")
    print(f"Frontend Login Success: {frontend_success}/{len(TEST_USERS)} ({frontend_success/len(TEST_USERS)*100:.1f}%)")
    
    if backend_success == len(TEST_USERS) and frontend_success == len(TEST_USERS):
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"   ✅ All simulation users can login through both backend and frontend")
        print(f"   ✅ Frontend login page should work correctly")
        print(f"\n🌐 You can now test manually at: {FRONTEND_URL}/login")
    elif backend_success == len(TEST_USERS):
        print(f"\n⚠️  BACKEND WORKS, FRONTEND ISSUES")
        print(f"   ✅ All users can login through backend")
        print(f"   ❌ Some users cannot login through frontend")
        print(f"   💡 Check frontend proxy configuration")
    else:
        print(f"\n❌ SOME TESTS FAILED")
        print(f"   💡 Check user credentials and database state")
        print(f"   💡 Ensure comprehensive simulation was run successfully")
    
    print(f"\n📋 Manual Testing Instructions:")
    print(f"   1. Open {FRONTEND_URL}/login in your browser")
    print(f"   2. Click any of the demo user buttons to auto-fill credentials")
    print(f"   3. Or manually enter any of these test credentials:")
    
    # Show first few users as examples
    for user in TEST_USERS[:3]:
        print(f"      - {user['email']} / {user['password']}")
    print(f"      - ... and {len(TEST_USERS)-3} more users")

if __name__ == "__main__":
    main()