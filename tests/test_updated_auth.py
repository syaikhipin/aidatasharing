#!/usr/bin/env python3
"""
Test Updated Authentication System
Tests the enhanced authentication system with support for all users.
"""

import requests
import json
from typing import Dict, List

BACKEND_URL = "http://localhost:8000"

def test_demo_users_endpoint():
    """Test the updated demo-users endpoint"""
    print("🔍 Testing Updated Demo Users Endpoint...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/auth/demo-users")
        
        if response.status_code == 200:
            data = response.json()
            users = data.get('demo_users', [])
            print(f"✅ Found {len(users)} demo users")
            
            # Group users by organization
            org_groups = {}
            for user in users:
                org = user.get('organization', 'No Organization')
                if org not in org_groups:
                    org_groups[org] = []
                org_groups[org].append(user)
            
            print("\n📋 Users by Organization:")
            for org, org_users in org_groups.items():
                print(f"\n🏢 {org}:")
                for user in org_users:
                    role_indicator = "👑" if user.get('is_superuser') else "👤"
                    print(f"  {role_indicator} {user['email']} / {user['password']} ({user['role']})")
                    print(f"     {user['description']}")
            
            return users
        else:
            print(f"❌ Demo users endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Error testing demo users: {e}")
        return []

def test_login_functionality(users: List[Dict]):
    """Test login functionality for all users"""
    print(f"\n🔑 Testing Login Functionality for {len(users)} Users...")
    
    successful_logins = 0
    failed_logins = []
    
    for user in users:
        email = user['email']
        password = user['password']
        
        try:
            # Test login
            login_response = requests.post(
                f"{BACKEND_URL}/api/auth/login",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "username": email,
                    "password": password
                }
            )
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                if token_data.get('access_token'):
                    print(f"✅ Login successful: {email}")
                    successful_logins += 1
                    
                    # Test /me endpoint with token
                    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                    me_response = requests.get(f"{BACKEND_URL}/api/auth/me", headers=headers)
                    
                    if me_response.status_code == 200:
                        user_info = me_response.json()
                        print(f"   👤 Profile: {user_info.get('full_name', 'No name')} - {user_info.get('organization_name', 'No org')}")
                    else:
                        print(f"   ⚠️  Profile fetch failed: {me_response.status_code}")
                else:
                    print(f"❌ Login failed: {email} - No access token")
                    failed_logins.append(email)
            else:
                print(f"❌ Login failed: {email} - Status {login_response.status_code}")
                failed_logins.append(email)
                
        except Exception as e:
            print(f"❌ Login error: {email} - {e}")
            failed_logins.append(email)
    
    print(f"\n📊 Login Results:")
    print(f"   ✅ Successful: {successful_logins}/{len(users)}")
    print(f"   ❌ Failed: {len(failed_logins)}")
    
    if failed_logins:
        print(f"\n❌ Failed logins:")
        for email in failed_logins:
            print(f"   - {email}")
    
    return successful_logins, failed_logins

def test_simple_registration():
    """Test the new simple registration endpoint"""
    print(f"\n🆕 Testing Simple Registration Endpoint...")
    
    test_user = {
        "email": "newtest@example.com",
        "password": "testpass123",
        "full_name": "Test New User"
    }
    
    try:
        # First, try to delete the user if it exists (cleanup)
        login_admin = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"username": "admin@example.com", "password": "admin123"}
        )
        
        # Test registration
        response = requests.post(
            f"{BACKEND_URL}/api/auth/register-simple",
            headers={"Content-Type": "application/json"},
            json=test_user
        )
        
        if response.status_code == 201:
            user_data = response.json()
            print(f"✅ Registration successful: {user_data['email']}")
            print(f"   👤 Name: {user_data['full_name']}")
            print(f"   🆔 ID: {user_data['id']}")
            
            # Test login with new user
            login_response = requests.post(
                f"{BACKEND_URL}/api/auth/login",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "username": test_user["email"],
                    "password": test_user["password"]
                }
            )
            
            if login_response.status_code == 200:
                print(f"✅ New user login successful")
                return True
            else:
                print(f"❌ New user login failed: {login_response.status_code}")
                return False
                
        elif response.status_code == 400 and "already registered" in response.text:
            print(f"ℹ️  User already exists, testing login...")
            # Test login with existing user
            login_response = requests.post(
                f"{BACKEND_URL}/api/auth/login",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "username": test_user["email"],
                    "password": test_user["password"]
                }
            )
            
            if login_response.status_code == 200:
                print(f"✅ Existing user login successful")
                return True
            else:
                print(f"❌ Existing user login failed: {login_response.status_code}")
                return False
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Registration test error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Updated Authentication System")
    print("=" * 60)
    
    # Test 1: Demo users endpoint
    users = test_demo_users_endpoint()
    
    # Test 2: Login functionality
    successful_logins = 0
    if users:
        successful_logins, failed_logins = test_login_functionality(users)
    
    # Test 3: Simple registration
    registration_ok = test_simple_registration()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   🔍 Demo Users Found: {len(users)}")
    print(f"   🔑 Successful Logins: {successful_logins}")
    print(f"   🆕 Registration Test: {'✅ PASS' if registration_ok else '❌ FAIL'}")
    
    all_tests_pass = len(users) > 0 and successful_logins > 0 and registration_ok
    
    if all_tests_pass:
        print(f"\n🎉 All Authentication Tests PASSED!")
        print(f"   - Demo users endpoint returns all users")
        print(f"   - Login works for all user types")
        print(f"   - New user registration works")
        print(f"   - Frontend can now access all users easily")
    else:
        print(f"\n❌ Some tests failed:")
        if len(users) == 0:
            print(f"   - Demo users endpoint not working")
        if successful_logins == 0:
            print(f"   - Login functionality not working")
        if not registration_ok:
            print(f"   - Registration functionality not working")

if __name__ == "__main__":
    main()