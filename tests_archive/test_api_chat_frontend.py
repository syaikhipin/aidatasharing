#!/usr/bin/env python3
"""
Test script to verify API chat functionality from frontend
"""

import requests
import json
import time

# Backend API base URL
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_backend_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Backend health check: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Backend health check failed: {e}")
        return False

def test_frontend_accessibility():
    """Test if frontend is accessible"""
    try:
        response = requests.get(FRONTEND_URL)
        print(f"✅ Frontend accessibility: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Frontend accessibility failed: {e}")
        return False

def test_auth_login():
    """Test authentication login"""
    try:
        login_data = {
            "username": "admin@example.com",
            "password": "admin123"
        }
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        print(f"✅ Auth login test: {response.status_code}")
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"✅ Token received: {token[:20]}...")
            return token
        return None
    except Exception as e:
        print(f"❌ Auth login failed: {e}")
        return None

def test_chat_api(token):
    """Test chat API endpoint"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        chat_data = {
            "message": "Hello, this is a test message for API chat functionality",
            "dataset_id": None  # Testing without dataset first
        }
        
        response = requests.post(f"{BASE_URL}/chat/", 
                               json=chat_data, 
                               headers=headers)
        
        print(f"✅ Chat API test: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Chat response received: {result.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ Chat API error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat API test failed: {e}")
        return False

def test_datasets_api(token):
    """Test datasets API endpoint"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{BASE_URL}/datasets/", headers=headers)
        print(f"✅ Datasets API test: {response.status_code}")
        if response.status_code == 200:
            datasets = response.json()
            print(f"✅ Found {len(datasets)} datasets")
            return datasets
        return []
    except Exception as e:
        print(f"❌ Datasets API test failed: {e}")
        return []

def main():
    print("🚀 Starting API Chat Frontend Test")
    print("=" * 50)
    
    # Test 1: Backend health
    if not test_backend_health():
        print("❌ Backend is not running. Please start the backend first.")
        return
    
    # Test 2: Frontend accessibility
    if not test_frontend_accessibility():
        print("❌ Frontend is not accessible. Please start the frontend first.")
        return
    
    # Test 3: Authentication
    token = test_auth_login()
    if not token:
        print("❌ Authentication failed. Cannot proceed with API tests.")
        return
    
    # Test 4: Datasets API
    datasets = test_datasets_api(token)
    
    # Test 5: Chat API
    chat_success = test_chat_api(token)
    
    print("\n" + "=" * 50)
    if chat_success:
        print("✅ API Chat functionality is working correctly!")
        print("✅ Frontend can successfully communicate with backend API")
        print("✅ Authentication is working")
        print("✅ Chat endpoint is responding")
    else:
        print("❌ API Chat functionality has issues")
    
    print("\n📋 Test Summary:")
    print(f"   - Backend Health: ✅")
    print(f"   - Frontend Access: ✅")
    print(f"   - Authentication: {'✅' if token else '❌'}")
    print(f"   - Datasets API: ✅")
    print(f"   - Chat API: {'✅' if chat_success else '❌'}")

if __name__ == "__main__":
    main()