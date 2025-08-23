#!/usr/bin/env python3
"""
Test Preview and Connector API Issues
Debug and fix the preview UI and connector API problems
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
FRONTEND_URL = "http://localhost:3000"

class PreviewConnectorTester:
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
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return None
    
    def test_existing_datasets(self):
        """Test preview functionality on existing datasets"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Get list of datasets
            response = requests.get(f"{BACKEND_URL}/api/datasets/", headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Failed to get datasets: {response.status_code}")
                return
            
            datasets = response.json()
            print(f"📊 Found {len(datasets)} datasets")
            
            if not datasets:
                print("❌ No datasets found to test")
                return
            
            # Test preview on first few datasets
            for i, dataset in enumerate(datasets[:3]):
                dataset_id = dataset['id']
                dataset_name = dataset['name']
                
                print(f"\n🔍 Testing dataset {dataset_id}: {dataset_name}")
                
                # Test preview endpoint
                preview_response = requests.get(
                    f"{BACKEND_URL}/api/datasets/{dataset_id}/preview",
                    headers=headers
                )
                
                print(f"   Preview API Status: {preview_response.status_code}")
                
                if preview_response.status_code == 200:
                    preview_data = preview_response.json()
                    preview = preview_data.get('preview', {})
                    
                    print(f"   ✅ Preview Data Available:")
                    print(f"      Type: {preview.get('type', 'unknown')}")
                    print(f"      Format: {preview.get('format', 'unknown')}")
                    print(f"      Source: {preview.get('source', 'unknown')}")
                    print(f"      Headers: {len(preview.get('headers', []))} columns")
                    print(f"      Rows: {preview.get('total_rows_in_preview', 0)} rows")
                    print(f"      Sample Data: {'Yes' if preview.get('rows') else 'No'}")
                    
                    # Check if this would work in UI
                    if preview.get('headers') and preview.get('rows'):
                        print(f"      ✅ UI Preview: Should work in frontend")
                    else:
                        print(f"      ❌ UI Preview: Missing data for frontend display")
                        print(f"         Missing headers: {not preview.get('headers')}")
                        print(f"         Missing rows: {not preview.get('rows')}")
                else:
                    print(f"   ❌ Preview failed: {preview_response.text}")
                    
        except Exception as e:
            print(f"❌ Dataset preview test failed: {e}")
    
    def test_connector_api_creation(self):
        """Test API connector creation and dataset generation"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            print(f"\n🔌 Testing API Connector Creation")
            
            # Create a simple API connector
            connector_data = {
                "name": "Test JSONPlaceholder API",
                "connector_type": "api", 
                "description": "Test API connector for debugging",
                "connection_config": {
                    "base_url": "https://jsonplaceholder.typicode.com",
                    "endpoint": "/posts",
                    "method": "GET",
                    "timeout": 30,
                    "headers": {}
                }
            }
            
            response = requests.post(
                f"{BACKEND_URL}/api/connectors/",
                headers=headers,
                json=connector_data
            )
            
            print(f"   Connector Creation Status: {response.status_code}")
            
            if response.status_code == 200:
                connector = response.json()
                connector_id = connector['id']
                print(f"   ✅ Connector created: ID {connector_id}")
                
                # Test the connector
                test_response = requests.post(
                    f"{BACKEND_URL}/api/connectors/{connector_id}/test",
                    headers=headers
                )
                
                print(f"   Connector Test Status: {test_response.status_code}")
                
                if test_response.status_code == 200:
                    test_result = test_response.json()
                    print(f"   ✅ Connector test: {test_result.get('success', False)}")
                    print(f"      Message: {test_result.get('message', 'No message')}")
                    
                    if test_result.get('success'):
                        # Try to create a dataset from this connector
                        dataset_data = {
                            "dataset_name": "Test API Dataset from Connector",
                            "description": "Dataset created from test API connector",
                            "table_or_endpoint": "/posts",
                            "sharing_level": "private"
                        }
                        
                        dataset_response = requests.post(
                            f"{BACKEND_URL}/api/connectors/{connector_id}/create-dataset",
                            headers=headers,
                            json=dataset_data
                        )
                        
                        print(f"   Dataset Creation Status: {dataset_response.status_code}")
                        
                        if dataset_response.status_code == 200:
                            dataset_result = dataset_response.json()
                            dataset_id = dataset_result.get('dataset_id')
                            print(f"   ✅ Dataset created: ID {dataset_id}")
                            
                            # Test preview on the new dataset
                            if dataset_id:
                                preview_response = requests.get(
                                    f"{BACKEND_URL}/api/datasets/{dataset_id}/preview",
                                    headers=headers
                                )
                                
                                print(f"   New Dataset Preview Status: {preview_response.status_code}")
                                
                                if preview_response.status_code == 200:
                                    preview_data = preview_response.json()
                                    preview = preview_data.get('preview', {})
                                    print(f"   ✅ New dataset preview works:")
                                    print(f"      Type: {preview.get('type', 'unknown')}")
                                    print(f"      Items: {preview.get('total_items_in_preview', 0)}")
                                    print(f"      MindsDB Integration: {preview.get('mindsdb_integration', False)}")
                                    
                                    return dataset_id
                                else:
                                    print(f"   ❌ New dataset preview failed: {preview_response.text}")
                        else:
                            print(f"   ❌ Dataset creation failed: {dataset_response.text}")
                    else:
                        print(f"   ❌ Connector test failed: {test_result.get('error', 'Unknown error')}")
                else:
                    print(f"   ❌ Connector test request failed: {test_response.text}")
            else:
                print(f"   ❌ Connector creation failed: {response.text}")
                
        except Exception as e:
            print(f"❌ API connector test failed: {e}")
            return None
    
    def create_test_dataset(self):
        """Create a simple test dataset for preview testing"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            print(f"\n📊 Creating Test Dataset for Preview")
            
            # Create test CSV data
            data = {
                'id': [1, 2, 3, 4, 5],
                'name': ['Alice', 'Bob', 'Carol', 'David', 'Eva'],
                'department': ['Engineering', 'Marketing', 'Sales', 'Engineering', 'HR'],
                'salary': [85000, 65000, 70000, 90000, 55000],
                'active': [True, True, False, True, True]
            }
            
            df = pd.DataFrame(data)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                df.to_csv(f.name, index=False)
                csv_file = f.name
            
            try:
                # Upload dataset
                with open(csv_file, 'rb') as f:
                    files = {"file": f}
                    data = {
                        "name": "Preview Test Dataset",
                        "description": "Test dataset for debugging preview functionality"
                    }
                    
                    response = requests.post(
                        f"{BACKEND_URL}/api/datasets/upload",
                        headers=headers,
                        files=files,
                        data=data
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    dataset = result.get('dataset', {})
                    dataset_id = dataset.get('id')
                    
                    print(f"   ✅ Test dataset created: ID {dataset_id}")
                    
                    # Test preview immediately
                    preview_response = requests.get(
                        f"{BACKEND_URL}/api/datasets/{dataset_id}/preview",
                        headers=headers
                    )
                    
                    print(f"   Preview Status: {preview_response.status_code}")
                    
                    if preview_response.status_code == 200:
                        preview_data = preview_response.json()
                        preview = preview_data.get('preview', {})
                        
                        print(f"   ✅ Preview working:")
                        print(f"      Type: {preview.get('type', 'unknown')}")
                        print(f"      Headers: {preview.get('headers', [])}")
                        print(f"      Rows: {len(preview.get('rows', []))}")
                        print(f"      Sample Row: {preview.get('rows', [{}])[0] if preview.get('rows') else 'None'}")
                        
                        return dataset_id
                    else:
                        print(f"   ❌ Preview failed: {preview_response.text}")
                else:
                    print(f"   ❌ Dataset upload failed: {response.text}")
                    
            finally:
                os.unlink(csv_file)
                
        except Exception as e:
            print(f"❌ Test dataset creation failed: {e}")
            return None
    
    def diagnose_preview_issues(self):
        """Diagnose specific preview issues"""
        print(f"\n🔍 Diagnosing Preview Issues")
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Get a dataset to test
            response = requests.get(f"{BACKEND_URL}/api/datasets/", headers=headers)
            
            if response.status_code == 200:
                datasets = response.json()
                if datasets:
                    dataset = datasets[0]
                    dataset_id = dataset['id']
                    
                    print(f"   Testing dataset {dataset_id}: {dataset['name']}")
                    
                    # Check dataset structure
                    print(f"   Dataset info:")
                    print(f"      Type: {dataset.get('type', 'unknown')}")
                    print(f"      Status: {dataset.get('status', 'unknown')}")
                    print(f"      File path: {dataset.get('source_url', 'None')}")
                    print(f"      Row count: {dataset.get('row_count', 'None')}")
                    print(f"      Column count: {dataset.get('column_count', 'None')}")
                    
                    # Test different preview calls
                    endpoints_to_test = [
                        f"/api/datasets/{dataset_id}/preview",
                        f"/api/datasets/{dataset_id}/preview?rows=10",
                        f"/api/datasets/{dataset_id}/preview?refresh=true",
                        f"/api/datasets/{dataset_id}/preview/enhanced"
                    ]
                    
                    for endpoint in endpoints_to_test:
                        response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers)
                        print(f"   {endpoint}: {response.status_code}")
                        
                        if response.status_code != 200:
                            print(f"      Error: {response.text[:200]}")
                        else:
                            data = response.json()
                            preview = data.get('preview', {})
                            print(f"      Has headers: {'headers' in preview}")
                            print(f"      Has rows: {'rows' in preview}")
                            print(f"      Preview type: {preview.get('type', 'unknown')}")
            
        except Exception as e:
            print(f"❌ Preview diagnosis failed: {e}")
    
    def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        print("🧪 Preview and Connector API Fix Test")
        print("=" * 50)
        
        # Step 1: Authentication
        print("\n1️⃣ Authentication Test")
        if not self.get_auth_token():
            print("❌ Authentication failed, stopping tests")
            return
        
        # Step 2: Test existing datasets
        print("\n2️⃣ Existing Dataset Preview Test")
        self.test_existing_datasets()
        
        # Step 3: Create test dataset
        print("\n3️⃣ New Dataset Creation and Preview Test")
        test_dataset_id = self.create_test_dataset()
        
        # Step 4: Test API connector
        print("\n4️⃣ API Connector Creation and Dataset Test")
        connector_dataset_id = self.test_connector_api_creation()
        
        # Step 5: Diagnose specific issues
        print("\n5️⃣ Preview Issue Diagnosis")
        self.diagnose_preview_issues()
        
        # Step 6: Summary
        print(f"\n📋 Test Summary")
        print("=" * 50)
        print(f"✅ Authentication: Working")
        print(f"📊 Test Dataset: {'Created' if test_dataset_id else 'Failed'}")
        print(f"🔌 API Connector Dataset: {'Created' if connector_dataset_id else 'Failed'}")
        
        print(f"\n🎯 Frontend Testing URLs:")
        if test_dataset_id:
            print(f"   Test Dataset: {FRONTEND_URL}/datasets/{test_dataset_id}")
        if connector_dataset_id:
            print(f"   Connector Dataset: {FRONTEND_URL}/datasets/{connector_dataset_id}")

def main():
    """Main test execution"""
    print("🧪 Preview and Connector API Fix Test Suite")
    print("Diagnosing UI preview and connector API issues")
    print("=" * 50)
    
    tester = PreviewConnectorTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()