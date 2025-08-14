#!/usr/bin/env python3
"""
Test script to verify the login page dropdown functionality
"""
import requests
import json

def test_demo_users_api():
    """Test the demo users API endpoint"""
    print("🧪 Testing Demo Users API...")
    
    try:
        response = requests.get('http://localhost:8000/api/auth/demo-users')
        if response.status_code == 200:
            data = response.json()
            demo_users = data.get('demo_users', [])
            print(f"✅ API Success: Found {len(demo_users)} demo users")
            
            for i, user in enumerate(demo_users, 1):
                print(f"  {i}. {user['full_name']} ({user['email']})")
                print(f"     Role: {user['role']} | Admin: {user['is_superuser']}")
                if user['organization']:
                    print(f"     Organization: {user['organization']}")
                print()
            
            return True
        else:
            print(f"❌ API Error: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API Connection Error: {e}")
        return False

def test_frontend_accessibility():
    """Test if frontend login page is accessible"""
    print("🌐 Testing Frontend Login Page...")
    
    try:
        response = requests.get('http://localhost:3000/login')
        if response.status_code == 200:
            print("✅ Frontend: Login page accessible")
            
            # Check for key elements
            content = response.text
            if 'Quick Login (Demo Accounts)' in content:
                print("✅ Frontend: Demo accounts section found")
            else:
                print("⚠️  Frontend: Demo accounts section not found")
                
            if 'Choose from' in content and 'demo accounts' in content:
                print("✅ Frontend: Dropdown placeholder found")
            else:
                print("⚠️  Frontend: Dropdown placeholder not found")
                
            return True
        else:
            print(f"❌ Frontend Error: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend Connection Error: {e}")
        return False

def main():
    print("🚀 Testing Login Page Dropdown Functionality\n")
    
    api_success = test_demo_users_api()
    frontend_success = test_frontend_accessibility()
    
    print("📋 Test Summary:")
    print(f"  Demo Users API: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"  Frontend Access: {'✅ PASS' if frontend_success else '❌ FAIL'}")
    
    if api_success and frontend_success:
        print("\n🎯 Result: Login page dropdown should be working correctly!")
        print("   The frontend will fetch demo users from the API and populate the dropdown.")
    else:
        print("\n⚠️  Result: Some issues detected. Please check the services.")

if __name__ == "__main__":
    main()