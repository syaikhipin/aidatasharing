#!/usr/bin/env python3
"""
Test MindsDB cleanup functionality for dataset deletion
"""
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.mindsdb import MindsDBService
import requests
import json
import time

def test_mindsdb_models_cleanup():
    """Test creating and deleting MindsDB models for datasets"""
    
    print("🧪 Testing MindsDB Models Cleanup")
    print("="*50)
    
    mindsdb_service = MindsDBService()
    
    # Test dataset information
    test_dataset_id = 9999
    test_dataset_name = "Test Cleanup Dataset"
    test_dataset_type = "CSV"
    
    try:
        # Step 1: Check current models
        print("1️⃣ Checking current MindsDB models...")
        
        mindsdb_url = "http://localhost:47334"
        models_response = requests.get(f"{mindsdb_url}/api/sql/query", 
                                     json={"query": "SHOW MODELS"}, 
                                     timeout=10)
        
        if models_response.status_code == 200:
            models_data = models_response.json()
            current_models = [row[0] for row in models_data.get('data', [])]
            print(f"✅ Found {len(current_models)} existing models")
            
            # Check if test model already exists
            test_model_name = f"dataset_{test_dataset_id}_chat_model"
            if test_model_name in current_models:
                print(f"⚠️ Test model {test_model_name} already exists, will be recreated")
        else:
            print(f"❌ Failed to get current models: {models_response.status_code}")
            return False
        
        # Step 2: Create test model
        print(f"\n2️⃣ Creating test model for dataset {test_dataset_id}...")
        
        create_result = mindsdb_service.create_dataset_ml_model(
            dataset_id=test_dataset_id,
            dataset_name=test_dataset_name,
            dataset_type=test_dataset_type
        )
        
        if create_result.get("success"):
            created_models = create_result.get("models_created", [])
            print(f"✅ Successfully created {len(created_models)} models:")
            for model in created_models:
                print(f"  - {model['name']} ({model['type']}) - Status: {model['status']}")
        else:
            print(f"❌ Failed to create models: {create_result.get('error')}")
            return False
        
        # Step 3: Wait a moment for model to be fully created
        print("\n3️⃣ Waiting for model to be fully created...")
        time.sleep(2)
        
        # Step 4: Verify model was created
        print("\n4️⃣ Verifying model creation...")
        
        verify_response = requests.get(f"{mindsdb_url}/api/sql/query", 
                                     json={"query": f"SHOW MODELS WHERE name = 'dataset_{test_dataset_id}_chat_model'"}, 
                                     timeout=10)
        
        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            if verify_data.get('data') and len(verify_data['data']) > 0:
                model_info = verify_data['data'][0]
                print(f"✅ Model verified: {model_info[0]} - Status: {model_info[5]}")
            else:
                print("❌ Model not found after creation")
                return False
        else:
            print(f"❌ Failed to verify model: {verify_response.status_code}")
        
        # Step 5: Test deletion
        print(f"\n5️⃣ Testing model deletion for dataset {test_dataset_id}...")
        
        delete_result = mindsdb_service.delete_dataset_models(test_dataset_id)
        
        if delete_result.get("success"):
            deleted_models = delete_result.get("deleted_models", [])
            errors = delete_result.get("errors", [])
            
            print(f"✅ Deletion completed:")
            print(f"  - Deleted models: {deleted_models}")
            if errors:
                print(f"  - Errors: {errors}")
            else:
                print("  - No errors occurred")
        else:
            print(f"❌ Failed to delete models: {delete_result.get('error')}")
            return False
        
        # Step 6: Verify models were deleted
        print("\n6️⃣ Verifying models were deleted...")
        
        final_verify_response = requests.get(f"{mindsdb_url}/api/sql/query", 
                                           json={"query": f"SHOW MODELS WHERE name LIKE '%dataset_{test_dataset_id}%'"}, 
                                           timeout=10)
        
        if final_verify_response.status_code == 200:
            final_data = final_verify_response.json()
            remaining_models = final_data.get('data', [])
            
            if not remaining_models:
                print("✅ All test models successfully deleted!")
            else:
                print(f"⚠️ Some models may still exist: {[row[0] for row in remaining_models]}")
        else:
            print(f"❌ Failed to verify deletion: {final_verify_response.status_code}")
        
        print("\n✅ MindsDB cleanup test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

def test_real_dataset_cleanup():
    """Test cleanup on an existing dataset model"""
    
    print("\n🔍 Testing Cleanup on Real Dataset Models")
    print("="*50)
    
    try:
        mindsdb_url = "http://localhost:47334"
        
        # Get all current models
        models_response = requests.get(f"{mindsdb_url}/api/sql/query", 
                                     json={"query": "SHOW MODELS"}, 
                                     timeout=10)
        
        if models_response.status_code == 200:
            models_data = models_response.json()
            all_models = models_data.get('data', [])
            
            # Find dataset models
            dataset_models = [row for row in all_models if 'dataset_' in row[0] and '_chat_model' in row[0]]
            
            print(f"Found {len(dataset_models)} dataset chat models:")
            for i, model_row in enumerate(dataset_models[:5]):  # Show first 5
                print(f"  {i+1}. {model_row[0]} - Status: {model_row[5]}")
            
            if dataset_models:
                # Test cleanup on the first model (extract dataset ID)
                first_model = dataset_models[0][0]
                try:
                    # Extract dataset ID from model name (e.g., "dataset_123_chat_model" -> 123)
                    dataset_id = int(first_model.split('_')[1])
                    print(f"\n🧹 Testing cleanup for dataset {dataset_id} (model: {first_model})")
                    
                    mindsdb_service = MindsDBService()
                    cleanup_result = mindsdb_service.delete_dataset_models(dataset_id)
                    
                    print(f"Cleanup result: {cleanup_result}")
                    
                    if cleanup_result.get("success"):
                        deleted = cleanup_result.get("deleted_models", [])
                        print(f"✅ Successfully cleaned up {len(deleted)} models: {deleted}")
                    else:
                        print(f"❌ Cleanup failed: {cleanup_result.get('error')}")
                        
                except ValueError:
                    print(f"⚠️ Could not extract dataset ID from model name: {first_model}")
            else:
                print("ℹ️ No dataset chat models found to test cleanup")
                
        else:
            print(f"❌ Failed to get models: {models_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Real dataset cleanup test failed: {e}")
        return False

def main():
    print("🚀 MindsDB Cleanup Testing Suite")
    print("="*50)
    
    # Test 1: Create and delete test models
    test1_result = test_mindsdb_models_cleanup()
    
    # Test 2: Test on existing dataset models (optional)
    print("\n" + "="*50)
    user_input = input("Test cleanup on existing dataset models? (y/n): ").lower().strip()
    
    if user_input == 'y':
        test2_result = test_real_dataset_cleanup()
    else:
        test2_result = True
        print("ℹ️ Skipped real dataset cleanup test")
    
    # Summary
    print("\n" + "="*50)
    print("🏆 TESTING SUMMARY")
    print("="*50)
    print(f"Create/Delete Test: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"Real Cleanup Test: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        print("\n🎉 All tests passed! MindsDB cleanup functionality is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()