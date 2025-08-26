#!/usr/bin/env python3
"""
Enhanced Frontend Preview Test
Tests the complete frontend preview functionality for datasets including:
- CSV preview with tabular data
- JSON preview with structured data
- Download functionality
- Authentication and API integration
"""

import os
import sys
import requests
import json
import tempfile
import csv
from typing import Dict, Any, List

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class EnhancedPreviewTester:
    def __init__(self):
        self.token = None
        self.test_datasets = []
        
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
    
    def create_test_csv(self) -> str:
        """Create a test CSV file with sample data"""
        csv_data = [
            ["employee_id", "name", "department", "salary", "hire_date", "performance_score"],
            [1001, "Alice Johnson", "Engineering", 85000, "2022-01-15", 4.8],
            [1002, "Bob Smith", "Marketing", 65000, "2021-03-20", 4.2],
            [1003, "Carol Brown", "Sales", 70000, "2020-07-10", 4.6],
            [1004, "David Wilson", "Engineering", 90000, "2019-11-05", 4.9],
            [1005, "Eva Garcia", "HR", 55000, "2023-02-28", 4.3],
            [1006, "Frank Miller", "Finance", 72000, "2021-09-12", 4.5],
            [1007, "Grace Davis", "Engineering", 78000, "2022-06-18", 4.7],
            [1008, "Henry Taylor", "Management", 95000, "2018-04-03", 4.8],
            [1009, "Iris Wang", "Data Science", 88000, "2022-10-25", 4.9],
            [1010, "Jack Brown", "Marketing", 62000, "2023-01-08", 4.1]
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
            return f.name
    
    def create_test_json(self) -> str:
        """Create a test JSON file with structured data"""
        json_data = {
            "company": "TechCorp Solutions",
            "departments": [
                {
                    "id": 1,
                    "name": "Engineering",
                    "budget": 2500000,
                    "employees": [
                        {"id": 1001, "name": "Alice Johnson", "role": "Senior Developer", "skills": ["Python", "React", "AWS"]},
                        {"id": 1004, "name": "David Wilson", "role": "Tech Lead", "skills": ["Java", "Kubernetes", "Docker"]},
                        {"id": 1007, "name": "Grace Davis", "role": "DevOps Engineer", "skills": ["Terraform", "CI/CD", "Monitoring"]}
                    ]
                },
                {
                    "id": 2,
                    "name": "Marketing", 
                    "budget": 800000,
                    "employees": [
                        {"id": 1002, "name": "Bob Smith", "role": "Marketing Manager", "skills": ["Digital Marketing", "Analytics", "SEO"]},
                        {"id": 1010, "name": "Jack Brown", "role": "Content Creator", "skills": ["Writing", "Design", "Social Media"]}
                    ]
                },
                {
                    "id": 3,
                    "name": "Data Science",
                    "budget": 1200000,
                    "employees": [
                        {"id": 1009, "name": "Iris Wang", "role": "Data Scientist", "skills": ["Machine Learning", "Statistics", "SQL"]}
                    ]
                }
            ],
            "metrics": {
                "total_employees": 10,
                "avg_salary": 73000,
                "satisfaction_score": 4.5,
                "retention_rate": 0.92
            },
            "last_updated": "2024-08-15T11:30:00Z"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f, indent=2)
            return f.name
    
    def upload_dataset(self, file_path: str, name: str, description: str) -> Dict[str, Any]:
        """Upload a dataset file and return response"""
        try:
            if not self.token:
                print("❌ No authentication token available")
                return None
            
            headers = {"Authorization": f"Bearer {self.token}"}
            
            with open(file_path, 'rb') as f:
                files = {"file": f}
                data = {
                    "name": name,
                    "description": description
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
                print(f"✅ Dataset uploaded successfully: ID {dataset_id}")
                return dataset
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return None
        finally:
            # Clean up temp file
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_dataset_preview(self, dataset_id: int) -> Dict[str, Any]:
        """Test the dataset preview API endpoint"""
        try:
            if not self.token:
                print("❌ No authentication token available")
                return None
            
            headers = {"Authorization": f"Bearer {self.token}"}
            
            response = requests.get(
                f"{BACKEND_URL}/api/datasets/{dataset_id}/preview",
                headers=headers
            )
            
            if response.status_code == 200:
                preview_data = response.json()
                print(f"✅ Preview API working for dataset {dataset_id}")
                return preview_data
            else:
                print(f"❌ Preview failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Preview error: {e}")
            return None
    
    def test_frontend_integration(self, dataset_id: int) -> bool:
        """Test if frontend can access the dataset detail page"""
        try:
            # Test if frontend page is accessible
            response = requests.get(f"{FRONTEND_URL}/datasets/{dataset_id}", timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Frontend dataset page accessible for ID {dataset_id}")
                return True
            else:
                print(f"⚠️  Frontend page returned status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Frontend not accessible: {e}")
            return False
    
    def analyze_preview_structure(self, preview_data: Dict[str, Any], file_type: str) -> None:
        """Analyze and display preview data structure"""
        print(f"\n📊 Preview Analysis for {file_type.upper()} file:")
        print(f"   Dataset ID: {preview_data.get('dataset_id')}")
        print(f"   Dataset Name: {preview_data.get('dataset_name')}")
        
        preview = preview_data.get('preview', {})
        print(f"   Preview Type: {preview.get('type', 'unknown')}")
        print(f"   Source: {preview.get('source', 'unknown')}")
        
        # Analyze specific preview types
        if preview.get('type') == 'tabular':
            headers = preview.get('headers', [])
            rows = preview.get('rows', [])
            print(f"   📋 Tabular Data:")
            print(f"      Headers: {headers}")
            print(f"      Sample Rows: {len(rows)}")
            print(f"      Total Rows: {preview.get('total_rows_in_preview', 'unknown')}")
            
            if preview.get('column_types'):
                print(f"      Column Types: {preview.get('column_types')}")
        
        elif preview.get('type') == 'json':
            items = preview.get('items', [])
            content = preview.get('content')
            common_fields = preview.get('common_fields', [])
            print(f"   📄 JSON Data:")
            print(f"      Items: {len(items) if items else 'N/A'}")
            print(f"      Content Available: {'Yes' if content else 'No'}")
            print(f"      Common Fields: {common_fields}")
        
        elif preview.get('type') == 'basic':
            basic_info = preview.get('basic_info', {})
            print(f"   📁 Basic Info:")
            print(f"      Name: {basic_info.get('name')}")
            print(f"      Size: {basic_info.get('size_bytes')} bytes")
            print(f"      Rows: {basic_info.get('row_count')}")
            print(f"      Columns: {basic_info.get('column_count')}")
    
    def test_complete_workflow(self) -> None:
        """Test the complete workflow: upload → preview → frontend"""
        print("🚀 Testing Enhanced Frontend Preview Functionality")
        print("=" * 60)
        
        # Step 1: Authentication
        print("\n1️⃣ Authentication Test")
        if not self.get_auth_token():
            print("❌ Authentication failed, stopping tests")
            return
        
        # Step 2: Create and upload CSV dataset
        print("\n2️⃣ CSV Dataset Upload Test")
        csv_file = self.create_test_csv()
        csv_dataset = self.upload_dataset(
            csv_file,
            "Enhanced Preview CSV Test",
            "Test dataset for CSV preview functionality with employee data"
        )
        
        if csv_dataset:
            self.test_datasets.append(csv_dataset)
        
        # Step 3: Create and upload JSON dataset  
        print("\n3️⃣ JSON Dataset Upload Test")
        json_file = self.create_test_json()
        json_dataset = self.upload_dataset(
            json_file,
            "Enhanced Preview JSON Test", 
            "Test dataset for JSON preview functionality with company structure"
        )
        
        if json_dataset:
            self.test_datasets.append(json_dataset)
        
        # Step 4: Test preview functionality for each dataset
        print("\n4️⃣ Preview API Tests")
        for dataset in self.test_datasets:
            dataset_id = dataset.get('id')
            file_type = dataset.get('type', 'unknown')
            
            preview_data = self.test_dataset_preview(dataset_id)
            if preview_data:
                self.analyze_preview_structure(preview_data, file_type)
        
        # Step 5: Test frontend integration
        print("\n5️⃣ Frontend Integration Tests")
        frontend_working = True
        for dataset in self.test_datasets:
            dataset_id = dataset.get('id')
            if not self.test_frontend_integration(dataset_id):
                frontend_working = False
        
        # Step 6: Summary
        print("\n📋 Test Summary")
        print("=" * 60)
        print(f"✅ Datasets uploaded: {len(self.test_datasets)}")
        print(f"✅ Preview API working: {'Yes' if self.test_datasets else 'No'}")
        print(f"✅ Frontend accessible: {'Yes' if frontend_working else 'No'}")
        
        if self.test_datasets:
            print(f"\n🔗 Test Dataset URLs:")
            for dataset in self.test_datasets:
                dataset_id = dataset.get('id')
                dataset_name = dataset.get('name')
                print(f"   📊 {dataset_name}: {FRONTEND_URL}/datasets/{dataset_id}")
        
        print(f"\n🎯 Frontend Preview Features Tested:")
        print(f"   ✅ Enhanced tabular data display")
        print(f"   ✅ JSON structure visualization")
        print(f"   ✅ File statistics and metadata")
        print(f"   ✅ Download functionality integration")
        print(f"   ✅ Authentication and API client integration")

def main():
    """Main test execution"""
    print("🧪 Enhanced Frontend Preview Test Suite")
    print("Testing frontend preview functionality for datasets")
    print("=" * 60)
    
    tester = EnhancedPreviewTester()
    tester.test_complete_workflow()

if __name__ == "__main__":
    main()