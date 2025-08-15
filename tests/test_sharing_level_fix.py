#!/usr/bin/env python3
"""
Test script to verify the sharing level update fix.
This script tests the dataset sharing level update functionality.
"""

import requests
import json
import sys
import os

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_DATASET_ID = 1  # Replace with an actual dataset ID for testing

def test_sharing_level_update():
    """Test updating dataset sharing levels"""
    print("🧪 Testing Dataset Sharing Level Update")
    print("=" * 50)
    
    # Test credentials - replace with actual test user credentials
    login_data = {
        "username": "jane.smith@techcorp.com",  # Replace with test user
        "password": "password123"
    }
    
    session = requests.Session()
    
    # Step 1: Login to get authentication token
    print("🔐 Step 1: Logging in...")
    try:
        login_response = session.post(
            f"{API_BASE_URL}/api/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
        
        auth_data = login_response.json()
        access_token = auth_data.get("access_token")
        
        if not access_token:
            print("❌ No access token received")
            return False
        
        print(f"✅ Login successful")
        
        # Set authorization header for subsequent requests
        session.headers.update({"Authorization": f"Bearer {access_token}"})
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 2: Get existing datasets to find a testable one
    print("📊 Step 2: Getting datasets...")
    try:
        datasets_response = session.get(f"{API_BASE_URL}/api/datasets")
        
        if datasets_response.status_code != 200:
            print(f"❌ Failed to get datasets: {datasets_response.status_code}")
            return False
        
        datasets = datasets_response.json()
        
        if not datasets:
            print("❌ No datasets found for testing")
            return False
        
        # Use first dataset for testing
        test_dataset = datasets[0]
        dataset_id = test_dataset["id"]
        current_sharing_level = test_dataset.get("sharing_level", "private")
        
        print(f"✅ Found test dataset: {test_dataset['name']} (ID: {dataset_id})")
        print(f"   Current sharing level: {current_sharing_level}")
        
    except Exception as e:
        print(f"❌ Error getting datasets: {e}")
        return False
    
    # Step 3: Test updating sharing levels
    print("🔄 Step 3: Testing sharing level updates...")
    
    test_levels = ["private", "organization", "public"]
    
    for new_level in test_levels:
        if new_level == current_sharing_level:
            continue  # Skip if already at this level
        
        print(f"   Testing update to '{new_level}'...")
        
        try:
            update_data = {"sharing_level": new_level}
            
            update_response = session.put(
                f"{API_BASE_URL}/api/datasets/{dataset_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if update_response.status_code == 200:
                updated_dataset = update_response.json()
                actual_level = updated_dataset.get("sharing_level")
                
                if actual_level == new_level:
                    print(f"   ✅ Successfully updated to '{new_level}'")
                else:
                    print(f"   ❌ Update failed: expected '{new_level}', got '{actual_level}'")
                    return False
            else:
                print(f"   ❌ API call failed: {update_response.status_code}")
                print(f"   Error: {update_response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error updating to '{new_level}': {e}")
            return False
        
        # Small delay between updates
        import time
        time.sleep(0.5)
    
    print("✅ All sharing level updates successful!")
    return True

def test_frontend_simulation():
    """Simulate the exact frontend API call"""
    print("\n🌐 Testing Frontend-like API Call")
    print("=" * 40)
    
    # This simulates exactly what the frontend does
    session = requests.Session()
    
    # Login (reuse logic from above)
    login_data = {
        "username": "jane.smith@techcorp.com",
        "password": "password123"
    }
    
    try:
        login_response = session.post(
            f"{API_BASE_URL}/api/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code == 200:
            auth_data = login_response.json()
            access_token = auth_data.get("access_token")
            session.headers.update({"Authorization": f"Bearer {access_token}"})
            print("✅ Frontend simulation: Login successful")
        else:
            print("❌ Frontend simulation: Login failed")
            return False
    
    except Exception as e:
        print(f"❌ Frontend simulation login error: {e}")
        return False
    
    # Get a dataset
    try:
        datasets_response = session.get(f"{API_BASE_URL}/api/datasets")
        datasets = datasets_response.json()
        
        if datasets:
            dataset_id = datasets[0]["id"]
            
            # Simulate exact frontend call
            frontend_payload = {"sharing_level": "organization"}
            
            response = session.put(
                f"{API_BASE_URL}/api/datasets/{dataset_id}",
                json=frontend_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print("✅ Frontend simulation: Sharing level update successful")
                result = response.json()
                print(f"   Updated level: {result.get('sharing_level')}")
                return True
            else:
                print(f"❌ Frontend simulation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Frontend simulation error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Dataset Sharing Level Update Tests")
    print("=" * 60)
    
    # Test 1: Basic sharing level updates
    test1_result = test_sharing_level_update()
    
    # Test 2: Frontend simulation
    test2_result = test_frontend_simulation()
    
    print("\n📋 Test Results Summary")
    print("=" * 30)
    print(f"Basic sharing level updates: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"Frontend simulation:        {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        print("\n🎉 All tests passed! The sharing level update fix is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the backend logs for more details.")
        print("\n💡 Debugging tips:")
        print("1. Ensure the backend is running on http://localhost:8000")
        print("2. Check that test user credentials are correct")
        print("3. Verify that test datasets exist and are accessible")
        print("4. Check backend logs for detailed error information")
        sys.exit(1)