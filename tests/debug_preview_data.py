#!/usr/bin/env python3
"""
Debug Preview Data Storage
Investigate exactly what's happening with preview data during upload
"""

import os
import sys
import requests
import json
import tempfile
import csv
import pandas as pd
from typing import Dict, Any, List

# Configuration
BACKEND_URL = "http://localhost:8000"

class PreviewDebugger:
    def __init__(self):
        self.token = None
        
    def get_auth_token(self) -> str:
        """Get authentication token for API calls"""
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/auth/login",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data="username=admin@example.com&password=SuperAdmin123!"
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                print("✅ Authentication successful")
                return self.token
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return None
    
    def create_and_debug_dataset(self):
        """Create a dataset and examine the actual stored data"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            print(f"\n🔍 Creating Dataset and Debugging Preview Data Storage")
            
            # Create simple test data
            data = {
                'id': [1, 2, 3],
                'name': ['Alice', 'Bob', 'Carol'],
                'score': [95, 87, 92]
            }
            
            df = pd.DataFrame(data)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                df.to_csv(f.name, index=False)
                csv_file = f.name
            
            try:
                # Upload dataset
                with open(csv_file, 'rb') as f:
                    files = {"file": f}
                    upload_data = {
                        "name": "Debug Dataset",
                        "description": "Dataset for debugging preview data storage"
                    }
                    
                    response = requests.post(
                        f"{BACKEND_URL}/api/datasets/upload",
                        headers=headers,
                        files=files,
                        data=upload_data
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    dataset = result.get('dataset', {})
                    dataset_id = dataset.get('id')
                    
                    print(f"   ✅ Dataset created: ID {dataset_id}")
                    
                    # Get the dataset details to see what was stored
                    dataset_response = requests.get(
                        f"{BACKEND_URL}/api/datasets/{dataset_id}",
                        headers=headers
                    )
                    
                    if dataset_response.status_code == 200:
                        dataset_details = dataset_response.json()
                        
                        print(f"\n📊 Dataset Details:")
                        print(f"   Name: {dataset_details.get('name')}")
                        print(f"   Type: {dataset_details.get('type')}")
                        print(f"   Row count: {dataset_details.get('row_count')}")
                        print(f"   Column count: {dataset_details.get('column_count')}")
                        print(f"   File path: {dataset_details.get('source_url')}")
                        
                        # Check preview_data field
                        preview_data = dataset_details.get('preview_data')
                        if preview_data:
                            print(f"\n📋 Stored Preview Data:")
                            print(f"   Headers: {preview_data.get('headers', [])}")
                            print(f"   Sample rows field: {preview_data.get('sample_rows', 'Not found')}")
                            print(f"   Rows field: {preview_data.get('rows', 'Not found')}")
                            print(f"   Total rows: {preview_data.get('total_rows', 'Not found')}")
                            print(f"   All keys: {list(preview_data.keys())}")
                        else:
                            print(f"\n❌ No preview_data found in dataset")
                        
                        # Check file_metadata field
                        file_metadata = dataset_details.get('file_metadata')
                        if file_metadata:
                            print(f"\n📁 File Metadata:")
                            print(f"   Sample data: {file_metadata.get('sample_data', 'Not found')}")
                            print(f"   Columns: {file_metadata.get('columns', 'Not found')}")
                            print(f"   All keys: {list(file_metadata.keys())}")
                        else:
                            print(f"\n❌ No file_metadata found in dataset")
                    
                    # Now test the preview API
                    print(f"\n🔍 Testing Preview API:")
                    preview_response = requests.get(
                        f"{BACKEND_URL}/api/datasets/{dataset_id}/preview",
                        headers=headers
                    )
                    
                    if preview_response.status_code == 200:
                        preview_api_data = preview_response.json()
                        preview = preview_api_data.get('preview', {})
                        
                        print(f"   Preview API Response:")
                        print(f"   Type: {preview.get('type')}")
                        print(f"   Format: {preview.get('format')}")
                        print(f"   Source: {preview.get('source')}")
                        print(f"   Headers: {preview.get('headers', [])}")
                        print(f"   Rows: {preview.get('rows', [])}")
                        print(f"   Total rows in preview: {preview.get('total_rows_in_preview', 'Not found')}")
                        print(f"   All preview keys: {list(preview.keys())}")
                        
                        # Test with refresh
                        refresh_response = requests.get(
                            f"{BACKEND_URL}/api/datasets/{dataset_id}/preview?refresh=true",
                            headers=headers
                        )
                        
                        if refresh_response.status_code == 200:
                            refresh_data = refresh_response.json()
                            refresh_preview = refresh_data.get('preview', {})
                            
                            print(f"\n🔄 Refresh Preview API Response:")
                            print(f"   Type: {refresh_preview.get('type')}")
                            print(f"   Source: {refresh_preview.get('source')}")
                            print(f"   Headers: {refresh_preview.get('headers', [])}")
                            print(f"   Rows: {refresh_preview.get('rows', [])}")
                    else:
                        print(f"   ❌ Preview API failed: {preview_response.status_code}")
                        print(f"   Error: {preview_response.text}")
                else:
                    print(f"   ❌ Dataset upload failed: {response.text}")
                    
            finally:
                os.unlink(csv_file)
                
        except Exception as e:
            print(f"❌ Debug process failed: {e}")
    
    def debug_existing_datasets(self):
        """Debug existing datasets to see their structure"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            print(f"\n🔍 Debugging Existing Datasets")
            
            # Get datasets
            response = requests.get(f"{BACKEND_URL}/api/datasets/", headers=headers)
            
            if response.status_code == 200:
                datasets = response.json()[:3]  # Check first 3
                
                for dataset in datasets:
                    dataset_id = dataset['id']
                    dataset_name = dataset['name']
                    
                    print(f"\n📊 Dataset {dataset_id}: {dataset_name}")
                    
                    # Get detailed info
                    detail_response = requests.get(
                        f"{BACKEND_URL}/api/datasets/{dataset_id}",
                        headers=headers
                    )
                    
                    if detail_response.status_code == 200:
                        details = detail_response.json()
                        
                        preview_data = details.get('preview_data')
                        if preview_data:
                            print(f"   Preview Data: {list(preview_data.keys())}")
                            if 'sample_rows' in preview_data:
                                print(f"   Sample rows count: {len(preview_data['sample_rows'])}")
                            if 'rows' in preview_data:
                                print(f"   Rows count: {len(preview_data['rows'])}")
                        else:
                            print(f"   No preview_data field")
                        
                        file_metadata = details.get('file_metadata')
                        if file_metadata and 'sample_data' in file_metadata:
                            print(f"   File metadata sample_data count: {len(file_metadata['sample_data'])}")
                        
                        # Test preview API
                        preview_response = requests.get(
                            f"{BACKEND_URL}/api/datasets/{dataset_id}/preview",
                            headers=headers
                        )
                        
                        if preview_response.status_code == 200:
                            preview_result = preview_response.json()
                            preview = preview_result.get('preview', {})
                            print(f"   API Preview: {len(preview.get('rows', []))} rows, source: {preview.get('source')}")
                        
        except Exception as e:
            print(f"❌ Existing dataset debug failed: {e}")
    
    def run_debug(self):
        """Run complete debug process"""
        print("🔍 Preview Data Storage Debug")
        print("=" * 40)
        
        # Step 1: Authentication
        if not self.get_auth_token():
            print("❌ Authentication failed, stopping debug")
            return
        
        # Step 2: Create and debug new dataset
        self.create_and_debug_dataset()
        
        # Step 3: Debug existing datasets
        self.debug_existing_datasets()

def main():
    """Main debug execution"""
    debugger = PreviewDebugger()
    debugger.run_debug()

if __name__ == "__main__":
    main()