#!/usr/bin/env python3
"""
Debug Upload Test - Step by Step

This script breaks down the upload process to identify exactly where the error occurs.
"""

import requests
import tempfile
import os
import json
import sys
sys.path.append('backend')

BASE_URL = "http://localhost:8000"

def test_debug():
    print("🔍 AI Share Platform - Debug Upload Test")
    print("=" * 60)
    
    # Get auth token first
    print("🔐 Getting authentication...")
    login_data = {"username": "testuser@example.com", "password": "password123"}
    login_response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    
    if login_response.status_code != 200:
        print("❌ Cannot authenticate")
        return
        
    token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Authenticated")
    
    # Test 1: Simple dataset creation (without file upload)
    print("\n🧪 Test 1: Simple Dataset Creation")
    
    simple_dataset = {
        "name": "Debug Test Dataset",
        "description": "Testing dataset creation without upload",
        "data_format": "CSV",
        "sharing_level": "PRIVATE",
        "columns": ["col1", "col2", "col3"],
        "row_count": 10
    }
    
    try:
        create_response = requests.post(f"{BASE_URL}/api/datasets/", json=simple_dataset, headers=headers)
        print(f"Dataset creation status: {create_response.status_code}")
        
        if create_response.status_code in [200, 201]:
            dataset = create_response.json()
            print(f"✅ Dataset created: ID {dataset.get('id')}")
        else:
            print(f"❌ Dataset creation failed: {create_response.text}")
            
    except Exception as e:
        print(f"❌ Exception in dataset creation: {e}")
    
    # Test 2: Test MindsDB service directly  
    print("\n🧪 Test 2: MindsDB Service Test")
    
    try:
        from backend.app.services.mindsdb import mindsdb_service
        
        # Test health
        health = mindsdb_service.health_check()
        print(f"MindsDB health: {health}")
        
        # Test file processing
        csv_content = "product,price\nLaptop,999.99\nPhone,599.99"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        
        result = mindsdb_service.process_file_content(temp_path, 'csv')
        print(f"✅ File processing: {result.get('success')}")
        
        os.unlink(temp_path)
        
    except Exception as e:
        print(f"❌ MindsDB error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Test database models
    print("\n🧪 Test 3: Database Models Test")
    
    try:
        from backend.app.models.dataset import Dataset, DatasetType, DatasetStatus
        from backend.app.models.organization import DataSharingLevel
        from backend.app.core.database import get_db
        
        # Test creating a dataset object
        db_gen = get_db()
        db = next(db_gen)
        
        test_dataset = Dataset(
            name="Debug Dataset",
            description="Debug test",
            type=DatasetType.CSV,
            status=DatasetStatus.ACTIVE,
            owner_id=1,  # Assuming user ID 1 exists
            organization_id=25,  # From previous test
            sharing_level=DataSharingLevel.PRIVATE,
            allow_download=True,
            allow_api_access=True
        )
        
        print("✅ Dataset model creation works")
        
    except Exception as e:
        print(f"❌ Database model error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Minimal upload test
    print("\n🧪 Test 4: Minimal Upload Test")
    
    csv_content = "product,price\nLaptop,999.99"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name
    
    try:
        with open(csv_file_path, 'rb') as f:
            files = {'file': ('minimal.csv', f, 'text/csv')}
            data = {
                'name': 'Minimal Test',
                'description': 'Minimal upload test',
                'sharing_level': 'private'  # lowercase
            }
            
            print("Sending minimal upload request...")
            upload_response = requests.post(
                f"{BASE_URL}/api/datasets/upload",
                files=files,
                data=data,
                headers=headers,
                timeout=30  # Longer timeout
            )
        
        print(f"Upload status: {upload_response.status_code}")
        
        if upload_response.status_code in [200, 201]:
            print("✅ Upload successful!")
            response_data = upload_response.json()
            print(f"Response keys: {list(response_data.keys())}")
        else:
            print(f"❌ Upload failed")
            print(f"Response headers: {dict(upload_response.headers)}")
            print(f"Response text: {upload_response.text}")
            
            # Try to parse error
            try:
                error_data = upload_response.json()
                print(f"Structured error: {json.dumps(error_data, indent=2)}")
            except:
                pass
    
    except Exception as e:
        print(f"❌ Upload exception: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if os.path.exists(csv_file_path):
            os.unlink(csv_file_path)
    
    print("\n" + "=" * 60)
    print("🔍 Debug test completed!")

if __name__ == "__main__":
    test_debug() 