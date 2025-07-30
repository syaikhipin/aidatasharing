#!/usr/bin/env python3
"""
Test Frontend API Client Environment Reload
Tests the frontend API client reload functionality
"""

import requests
import json
import sys

def test_frontend_api_client():
    """Test the frontend API client environment reload"""
    
    print("🧪 Testing Frontend API Client Environment Reload")
    print("=" * 60)
    
    # Backend URL
    backend_url = "http://localhost:8000"
    
    try:
        # Step 1: Login to get token
        print("🔐 Logging in as admin...")
        login_data = {
            'username': 'admin@example.com',
            'password': 'admin123'
        }
        
        login_response = requests.post(
            f"{backend_url}/api/auth/login",
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
        
        login_result = login_response.json()
        token = login_result.get('access_token')
        
        if not token:
            print("❌ No access token received")
            return False
        
        print("✅ Login successful")
        
        # Step 2: Test environment reload endpoint directly
        print("🔄 Testing environment reload endpoint...")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        reload_response = requests.post(
            f"{backend_url}/api/admin/environment/environment-variables/reload",
            headers=headers
        )
        
        if reload_response.status_code != 200:
            print(f"❌ Environment reload failed: {reload_response.status_code}")
            print(f"Response: {reload_response.text}")
            return False
        
        reload_result = reload_response.json()
        print(f"✅ Environment reload successful")
        print(f"   Reloaded {reload_result.get('total_variables_reloaded', 0)} variables")
        
        # Step 3: Test environment variables endpoint
        print("📋 Testing environment variables endpoint...")
        
        env_response = requests.get(
            f"{backend_url}/api/admin/environment/environment-variables",
            headers=headers
        )
        
        if env_response.status_code != 200:
            print(f"❌ Environment variables failed: {env_response.status_code}")
            print(f"Response: {env_response.text}")
            return False
        
        env_result = env_response.json()
        print(f"✅ Environment variables retrieved")
        print(f"   Total variables: {env_result.get('total_variables', 0)}")
        
        # Step 4: Test with axios-like request (simulating frontend)
        print("🌐 Testing with frontend-like request...")
        
        # Simulate axios request with proper headers
        axios_headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        axios_response = requests.post(
            f"{backend_url}/api/admin/environment/environment-variables/reload",
            headers=axios_headers,
            json={}  # Empty JSON body like axios would send
        )
        
        if axios_response.status_code != 200:
            print(f"❌ Axios-like request failed: {axios_response.status_code}")
            print(f"Response: {axios_response.text}")
            print(f"Headers sent: {axios_headers}")
            return False
        
        axios_result = axios_response.json()
        print(f"✅ Axios-like request successful")
        print(f"   Reloaded {axios_result.get('total_variables_reloaded', 0)} variables")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

def main():
    """Main test runner"""
    success = test_frontend_api_client()
    
    if success:
        print("\n🎉 All frontend API client tests passed!")
        print("\n💡 Possible frontend issues:")
        print("   1. Token storage inconsistency (access_token vs token)")
        print("   2. CORS issues")
        print("   3. Frontend not using updated API client")
        print("   4. Browser cache issues")
        print("\n🔧 Recommended actions:")
        print("   1. Clear browser localStorage and cookies")
        print("   2. Hard refresh the frontend (Ctrl+Shift+R)")
        print("   3. Check browser console for detailed error messages")
        print("   4. Verify the frontend is using the updated API client")
        return 0
    else:
        print("\n❌ Frontend API client tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)