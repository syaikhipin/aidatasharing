#!/usr/bin/env python3
"""
Test script to verify storage service functionality
"""

import os
import sys
import asyncio
import json
import pandas as pd
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.services.storage import storage_service

# Create test files
def create_test_files():
    """Create test files for different formats"""
    test_dir = Path("./test_files")
    test_dir.mkdir(exist_ok=True)
    
    # Create CSV file
    csv_path = test_dir / "test.csv"
    df = pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'age': [25, 30, 35],
        'city': ['New York', 'Los Angeles', 'Chicago']
    })
    df.to_csv(csv_path, index=False)
    
    # Create JSON file
    json_path = test_dir / "test.json"
    data = {
        'users': [
            {'name': 'Alice', 'age': 25, 'city': 'New York'},
            {'name': 'Bob', 'age': 30, 'city': 'Los Angeles'},
            {'name': 'Charlie', 'age': 35, 'city': 'Chicago'}
        ],
        'metadata': {
            'count': 3,
            'version': '1.0'
        }
    }
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Create TXT file
    txt_path = test_dir / "test.txt"
    with open(txt_path, 'w') as f:
        f.write("This is a test text file.\nIt has multiple lines.\nLine 3 is here.")
    
    return {
        'csv': csv_path,
        'json': json_path,
        'txt': txt_path
    }

# Test storage service
async def test_storage_service(file_paths):
    """Test storage service functionality"""
    print("\n=== Testing Storage Service ===")
    
    results = {}
    
    for file_type, file_path in file_paths.items():
        print(f"\nTesting {file_type.upper()} file:")
        
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Store file
        try:
            store_result = await storage_service.store_dataset_file(
                file_content=file_content,
                original_filename=file_path.name,
                dataset_id=1,
                organization_id=1
            )
            print(f"✅ Store {file_type} file: Success")
            print(f"   - Stored at: {store_result['file_path']}")
            print(f"   - Size: {store_result['file_size']} bytes")
            
            # Retrieve file
            retrieved_path = await storage_service.retrieve_dataset_file(store_result['file_path'])
            if retrieved_path:
                print(f"✅ Retrieve {file_type} file: Success")
                print(f"   - Retrieved from: {retrieved_path}")
            else:
                print(f"❌ Retrieve {file_type} file: Failed")
            
            # Generate download token
            token = storage_service.generate_download_token(dataset_id=1, user_id=1)
            print(f"✅ Generate download token: {token}")
            
            # Validate token
            is_valid = storage_service.validate_download_token(token)
            print(f"✅ Validate token: {'Valid' if is_valid else 'Invalid'}")
            
            # Store result for further testing
            results[file_type] = {
                'file_path': store_result['file_path'],
                'token': token
            }
            
        except Exception as e:
            print(f"❌ Error testing {file_type} file: {e}")
    
    return results

async def main():
    """Main test function"""
    print("Starting tests for storage service functionality...")
    
    # Create test files
    file_paths = create_test_files()
    print(f"Created test files: {', '.join(file_paths.keys())}")
    
    # Test storage service
    await test_storage_service(file_paths)
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(main())