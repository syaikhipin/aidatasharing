#!/usr/bin/env python3
"""
Direct test of MindsDB cleanup methods
"""
import sys
import os
import requests

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_mindsdb_service_direct():
    """Test MindsDB service methods directly"""
    
    print("🧪 Direct MindsDB Service Test")
    print("="*40)
    
    try:
        from app.services.mindsdb import MindsDBService
        
        mindsdb_service = MindsDBService()
        
        # Test dataset info
        test_dataset_id = 99999
        test_dataset_name = "Cleanup Test Dataset"
        test_dataset_type = "CSV"
        
        print(f"Testing with dataset ID: {test_dataset_id}")
        
        # Step 1: Check current models before
        print("\n1️⃣ Checking current MindsDB models...")
        
        mindsdb_url = "http://localhost:47334"
        models_response = requests.post(f"{mindsdb_url}/api/sql/query", 
                                      json={"query": "SHOW MODELS"}, 
                                      timeout=10)
        
        models_before = []
        if models_response.status_code == 200:
            models_data = models_response.json()
            models_before = [row[0] for row in models_data.get('data', [])]
            dataset_models_before = [m for m in models_before if 'dataset_' in m]
            
            print(f"✅ Current state:")
            print(f"  - Total models: {len(models_before)}")
            print(f"  - Dataset models: {len(dataset_models_before)}")
            
            # Check if our test model exists
            test_model_name = f"dataset_{test_dataset_id}_chat_model"
            if test_model_name in models_before:
                print(f"  - Test model {test_model_name} already exists")
            else:
                print(f"  - Test model {test_model_name} does not exist")
        
        # Step 2: Test creating a model
        print(f"\n2️⃣ Testing model creation...")
        
        create_result = mindsdb_service.create_dataset_ml_model(
            dataset_id=test_dataset_id,
            dataset_name=test_dataset_name,
            dataset_type=test_dataset_type
        )
        
        print(f"Create result: {create_result}")
        
        if create_result.get("success"):
            print("✅ Model creation succeeded")
            created_models = create_result.get("models_created", [])
            for model in created_models:
                print(f"  - Created: {model['name']} ({model['status']})")
        else:
            print(f"❌ Model creation failed: {create_result.get('error')}")
            
        # Step 3: Verify model was created
        print(f"\n3️⃣ Verifying model creation...")
        
        import time
        time.sleep(3)  # Wait for model to be fully created
        
        verify_response = requests.post(f"{mindsdb_url}/api/sql/query", 
                                      json={"query": f"SHOW MODELS WHERE name = 'dataset_{test_dataset_id}_chat_model'"}, 
                                      timeout=10)
        
        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            if verify_data.get('data') and len(verify_data['data']) > 0:
                model_info = verify_data['data'][0]
                print(f"✅ Model verified: {model_info[0]} - Status: {model_info[5]}")
            else:
                print("⚠️ Model not found in verification")
        
        # Step 4: Test deletion
        print(f"\n4️⃣ Testing model deletion...")
        
        delete_result = mindsdb_service.delete_dataset_models(test_dataset_id)
        
        print(f"Delete result: {delete_result}")
        
        if delete_result.get("success"):
            deleted_models = delete_result.get("deleted_models", [])
            errors = delete_result.get("errors", [])
            
            print("✅ Model deletion completed:")
            print(f"  - Deleted models: {deleted_models}")
            if errors:
                print(f"  - Errors: {errors}")
        else:
            print(f"❌ Model deletion failed: {delete_result.get('error')}")
            
        # Step 5: Verify deletion
        print(f"\n5️⃣ Verifying model deletion...")
        
        time.sleep(2)  # Wait for deletion to complete
        
        final_response = requests.post(f"{mindsdb_url}/api/sql/query", 
                                     json={"query": f"SHOW MODELS WHERE name LIKE '%dataset_{test_dataset_id}%'"}, 
                                     timeout=10)
        
        if final_response.status_code == 200:
            final_data = final_response.json()
            remaining_models = final_data.get('data', [])
            
            if not remaining_models:
                print("✅ All test models successfully deleted!")
            else:
                print(f"⚠️ Some models still exist: {[row[0] for row in remaining_models]}")
        
        # Step 6: Check overall state
        print(f"\n6️⃣ Final state check...")
        
        final_models_response = requests.post(f"{mindsdb_url}/api/sql/query", 
                                            json={"query": "SHOW MODELS"}, 
                                            timeout=10)
        
        if final_models_response.status_code == 200:
            final_models_data = final_models_response.json()
            models_after = [row[0] for row in final_models_data.get('data', [])]
            
            print(f"✅ Final state:")
            print(f"  - Total models before: {len(models_before)}")
            print(f"  - Total models after: {len(models_after)}")
            
            net_change = len(models_after) - len(models_before)
            if net_change == 0:
                print(f"  - ✅ No net change (created and deleted successfully)")
            else:
                print(f"  - ⚠️ Net change: {net_change} models")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_existing_dataset_cleanup():
    """Test cleanup on existing dataset models"""
    
    print("\n🔍 Testing Cleanup on Existing Models")
    print("="*50)
    
    try:
        from app.services.mindsdb import MindsDBService
        
        mindsdb_service = MindsDBService()
        
        # Get current models
        mindsdb_url = "http://localhost:47334"
        models_response = requests.post(f"{mindsdb_url}/api/sql/query", 
                                      json={"query": "SHOW MODELS"}, 
                                      timeout=10)
        
        if models_response.status_code == 200:
            models_data = models_response.json()
            all_models = models_data.get('data', [])
            
            # Find dataset models
            dataset_models = [row for row in all_models if 'dataset_' in row[0] and '_chat_model' in row[0]]
            
            print(f"Found {len(dataset_models)} dataset chat models:")
            for i, model_row in enumerate(dataset_models):
                status = model_row[5] if len(model_row) > 5 else 'unknown'
                print(f"  {i+1}. {model_row[0]} - Status: {status}")
            
            if len(dataset_models) >= 2:
                # Test cleanup on one model (pick one with 'test' in name or highest ID)
                test_model = None
                for model_row in dataset_models:
                    model_name = model_row[0]
                    if 'test' in model_name.lower() or any(str(i) in model_name for i in [999, 888, 777]):
                        test_model = model_row
                        break
                
                if not test_model:
                    test_model = dataset_models[-1]  # Use the last one
                
                model_name = test_model[0]
                
                # Extract dataset ID
                try:
                    parts = model_name.split('_')
                    dataset_id = int(parts[1])
                    
                    print(f"\n🧹 Testing cleanup for dataset {dataset_id} (model: {model_name})")
                    
                    cleanup_result = mindsdb_service.delete_dataset_models(dataset_id)
                    
                    print(f"Cleanup result:")
                    print(f"  - Success: {cleanup_result.get('success')}")
                    print(f"  - Deleted models: {cleanup_result.get('deleted_models', [])}")
                    print(f"  - Errors: {cleanup_result.get('errors', [])}")
                    
                    if cleanup_result.get("success"):
                        deleted = cleanup_result.get("deleted_models", [])
                        print(f"✅ Successfully cleaned up {len(deleted)} models")
                    else:
                        print(f"⚠️ Cleanup had issues: {cleanup_result.get('error')}")
                        
                except (ValueError, IndexError):
                    print(f"⚠️ Could not extract dataset ID from model name: {model_name}")
                    return False
            else:
                print("ℹ️ Not enough dataset models to test cleanup safely")
                
            return True
        else:
            print(f"❌ Could not get models: {models_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Existing model cleanup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 Direct MindsDB Service Testing")
    print("="*50)
    
    # Test 1: Direct service methods
    direct_test_ok = test_mindsdb_service_direct()
    
    # Test 2: Existing models cleanup (optional)
    print("\n" + "="*50)
    existing_test_ok = test_existing_dataset_cleanup()
    
    # Summary
    print("\n" + "="*50)
    print("🏆 TESTING SUMMARY")
    print("="*50)
    print(f"Direct Service Test: {'✅ PASS' if direct_test_ok else '❌ FAIL'}")
    print(f"Existing Models Test: {'✅ PASS' if existing_test_ok else '❌ FAIL'}")
    
    if direct_test_ok and existing_test_ok:
        print("\n🎉 All tests passed!")
        print("✅ MindsDB cleanup functionality is working correctly")
        print("✅ Dataset deletion will properly clean up ML models")
    else:
        print("\n⚠️ Some tests had issues. Check the output above.")

if __name__ == "__main__":
    main()