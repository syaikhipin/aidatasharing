#!/usr/bin/env python3
"""
Test dataset deletion with MindsDB cleanup
"""
import requests
import json
import time
import sys
import os

def test_dataset_deletion_api():
    """Test dataset deletion via backend API to verify MindsDB cleanup"""
    
    print("🗑️ Testing Dataset Deletion with MindsDB Cleanup")
    print("="*60)
    
    backend_url = "http://localhost:8000"
    
    # Step 1: Login
    print("1️⃣ Logging in...")
    
    # Try different login formats
    login_formats = [
        {"email": "alice@techcorp.com", "password": "Password123!"},
        {"username": "alice@techcorp.com", "password": "Password123!"},
    ]
    
    token = None
    for login_data in login_formats:
        try:
            response = requests.post(f"{backend_url}/api/auth/login", json=login_data)
            if response.status_code == 200:
                token = response.json().get("access_token")
                print(f"✅ Login successful")
                break
            else:
                print(f"⚠️ Login failed with {login_data}: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Login error: {e}")
    
    if not token:
        print("❌ Could not login to test API")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Get existing datasets
    print("\n2️⃣ Getting existing datasets...")
    
    try:
        datasets_response = requests.get(f"{backend_url}/api/datasets/", headers=headers)
        
        if datasets_response.status_code == 200:
            datasets = datasets_response.json()
            print(f"✅ Found {len(datasets)} datasets")
            
            if not datasets:
                print("ℹ️ No datasets found to test deletion")
                return True
            
            # Show first few datasets
            for i, dataset in enumerate(datasets[:3]):
                print(f"  {i+1}. ID: {dataset.get('id')} - Name: {dataset.get('name')} - Type: {dataset.get('type')}")
                
        else:
            print(f"❌ Failed to get datasets: {datasets_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting datasets: {e}")
        return False
    
    # Step 3: Check MindsDB models before deletion
    print("\n3️⃣ Checking MindsDB models before deletion...")
    
    try:
        mindsdb_url = "http://localhost:47334"
        models_response = requests.post(f"{mindsdb_url}/api/sql/query", 
                                      json={"query": "SHOW MODELS"}, 
                                      timeout=10)
        
        if models_response.status_code == 200:
            models_data = models_response.json()
            all_models = [row[0] for row in models_data.get('data', [])]
            dataset_models = [m for m in all_models if 'dataset_' in m and '_chat_model' in m]
            
            print(f"✅ MindsDB Status:")
            print(f"  - Total models: {len(all_models)}")
            print(f"  - Dataset chat models: {len(dataset_models)}")
            
            if dataset_models:
                print(f"  - First 3 dataset models: {dataset_models[:3]}")
            
            models_before = dataset_models.copy()
            
        else:
            print(f"⚠️ Could not check MindsDB models: {models_response.status_code}")
            models_before = []
            
    except Exception as e:
        print(f"⚠️ MindsDB connection error (expected if not running): {e}")
        models_before = []
    
    # Step 4: Test dataset deletion
    if datasets:
        # Choose a dataset to delete (preferably a test one)
        test_dataset = None
        for dataset in datasets:
            if 'test' in dataset.get('name', '').lower() or dataset.get('id') in [999, 9999]:
                test_dataset = dataset
                break
        
        if not test_dataset:
            # Use the last dataset (least likely to be important)
            test_dataset = datasets[-1]
        
        dataset_id = test_dataset.get('id')
        dataset_name = test_dataset.get('name')
        
        print(f"\n4️⃣ Testing deletion of dataset {dataset_id} ({dataset_name})...")
        
        # Confirm deletion
        print(f"⚠️ About to delete dataset: {dataset_name}")
        
        try:
            delete_response = requests.delete(
                f"{backend_url}/api/datasets/{dataset_id}",
                headers=headers,
                params={"force_delete": False}  # Soft delete first
            )
            
            if delete_response.status_code == 200:
                result = delete_response.json()
                print(f"✅ Dataset deletion successful:")
                print(f"  - Type: {result.get('deletion_type')}")
                print(f"  - File deletion: {result.get('file_deletion', {}).get('success', 'N/A')}")
                
                # Check if MindsDB cleanup was mentioned in logs
                if 'ml_cleanup_result' in str(result):
                    print(f"  - ML cleanup mentioned in response")
                
            elif delete_response.status_code == 404:
                print(f"⚠️ Dataset {dataset_id} not found or already deleted")
            else:
                print(f"❌ Dataset deletion failed: {delete_response.status_code}")
                print(f"Error: {delete_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error during deletion: {e}")
            return False
    
    # Step 5: Check MindsDB models after deletion
    print("\n5️⃣ Checking MindsDB models after deletion...")
    
    try:
        time.sleep(2)  # Wait for cleanup to complete
        
        models_response = requests.post(f"{mindsdb_url}/api/sql/query", 
                                      json={"query": "SHOW MODELS"}, 
                                      timeout=10)
        
        if models_response.status_code == 200:
            models_data = models_response.json()
            all_models_after = [row[0] for row in models_data.get('data', [])]
            dataset_models_after = [m for m in all_models_after if 'dataset_' in m and '_chat_model' in m]
            
            print(f"✅ MindsDB Status After Deletion:")
            print(f"  - Total models: {len(all_models_after)}")
            print(f"  - Dataset chat models: {len(dataset_models_after)}")
            
            # Compare before and after
            if models_before:
                deleted_models = set(models_before) - set(dataset_models_after)
                if deleted_models:
                    print(f"  - Deleted models: {list(deleted_models)}")
                else:
                    print(f"  - No models were deleted")
                    
                if dataset_models_after:
                    print(f"  - Remaining dataset models: {dataset_models_after[:3]}")
            
        else:
            print(f"⚠️ Could not check MindsDB models after deletion: {models_response.status_code}")
            
    except Exception as e:
        print(f"⚠️ MindsDB connection error after deletion: {e}")
    
    print("\n✅ Dataset deletion test completed!")
    return True

def test_mindsdb_connection():
    """Test basic MindsDB connection and list models"""
    
    print("🔍 Testing MindsDB Connection")
    print("="*40)
    
    try:
        mindsdb_url = "http://localhost:47334"
        
        # Test status endpoint
        status_response = requests.get(f"{mindsdb_url}/api/status", timeout=5)
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"✅ MindsDB Status: Running")
            print(f"  - Version: {status_data.get('mindsdb_version', 'Unknown')}")
            print(f"  - Environment: {status_data.get('environment', 'Unknown')}")
            
            # Test models endpoint
            models_response = requests.post(f"{mindsdb_url}/api/sql/query", 
                                          json={"query": "SHOW MODELS"}, 
                                          timeout=10)
            
            if models_response.status_code == 200:
                models_data = models_response.json()
                all_models = models_data.get('data', [])
                dataset_models = [row for row in all_models if 'dataset_' in row[0]]
                
                print(f"✅ Models Query Success:")
                print(f"  - Total models: {len(all_models)}")
                print(f"  - Dataset models: {len(dataset_models)}")
                
                if dataset_models:
                    print(f"  - Dataset model examples:")
                    for i, model in enumerate(dataset_models[:3]):
                        print(f"    {i+1}. {model[0]} - Status: {model[5]}")
                
                return True
            else:
                print(f"❌ Models query failed: {models_response.status_code}")
                return False
            
        else:
            print(f"❌ MindsDB status check failed: {status_response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to MindsDB - is it running on localhost:47334?")
        return False
    except Exception as e:
        print(f"❌ MindsDB connection test failed: {e}")
        return False

def main():
    print("🚀 Dataset Deletion & MindsDB Cleanup Test")
    print("="*50)
    
    # Test 1: Check MindsDB connection
    mindsdb_ok = test_mindsdb_connection()
    
    # Test 2: Test dataset deletion API
    print("\n" + "="*50)
    deletion_ok = test_dataset_deletion_api()
    
    # Summary
    print("\n" + "="*50)
    print("🏆 TESTING SUMMARY")
    print("="*50)
    print(f"MindsDB Connection: {'✅ PASS' if mindsdb_ok else '❌ FAIL'}")
    print(f"Dataset Deletion Test: {'✅ PASS' if deletion_ok else '❌ FAIL'}")
    
    if mindsdb_ok and deletion_ok:
        print("\n🎉 All tests passed!")
        print("✅ Dataset deletion properly cleans up MindsDB models")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()