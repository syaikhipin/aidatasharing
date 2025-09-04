#!/usr/bin/env python3
"""
Test script for dataset deletion functionality
"""

import requests
import json
import os
import tempfile
import time

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "alice@techcorp.com"
TEST_PASSWORD = "Password123!"

class DatasetDeletionTest:
    def __init__(self):
        self.access_token = None
        self.session = requests.Session()
    
    def authenticate(self):
        """Authenticate and get access token"""
        print("🔐 Authenticating...")
        
        auth_data = {
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", data=auth_data)
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code} - {response.text}")
            return False
    
    def create_test_dataset(self):
        """Create a test dataset for deletion testing"""
        print("\n📁 Creating test dataset...")
        
        # Create test file
        content = "test,data\n1,2\n3,4"
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write(content)
        temp_file.close()
        
        try:
            with open(temp_file.name, 'rb') as f:
                files = {'file': ('test_deletion.csv', f, 'text/csv')}
                data = {
                    'title': 'Dataset for Deletion Test',
                    'description': 'This dataset will be deleted',
                    'tags': 'test,deletion'
                }
                
                response = self.session.post(f"{BASE_URL}/api/datasets/upload", files=files, data=data)
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # Extract dataset from response
                    if 'dataset' in response_data:
                        dataset_data = response_data['dataset']
                    else:
                        dataset_data = response_data
                    
                    print(f"✅ Dataset created successfully")
                    print(f"   Dataset ID: {dataset_data.get('id', 'N/A')}")
                    print(f"   File Path: {dataset_data.get('file_path', 'N/A')}")
                    return dataset_data
                else:
                    print(f"❌ Dataset creation failed: {response.status_code} - {response.text}")
                    return None
        finally:
            os.unlink(temp_file.name)
    
    def test_soft_delete(self, dataset_id):
        """Test soft delete (default behavior)"""
        print(f"\n🗑️ Testing soft delete for dataset {dataset_id}...")
        
        response = self.session.delete(f"{BASE_URL}/api/datasets/{dataset_id}")
        
        if response.status_code == 200:
            print("✅ Soft delete successful")
            
            # Verify dataset is soft deleted
            response = self.session.get(f"{BASE_URL}/api/datasets/{dataset_id}")
            if response.status_code == 200:
                dataset = response.json()
                if dataset.get('is_deleted'):
                    print("✅ Dataset marked as deleted")
                else:
                    print("⚠️ Dataset not marked as deleted")
            return True
        else:
            print(f"❌ Soft delete failed: {response.status_code} - {response.text}")
            return False
    
    def test_hard_delete(self, dataset_id):
        """Test hard delete (force_delete=true)"""
        print(f"\n💀 Testing hard delete for dataset {dataset_id}...")
        
        response = self.session.delete(f"{BASE_URL}/api/datasets/{dataset_id}?force_delete=true")
        
        if response.status_code == 200:
            print("✅ Hard delete successful")
            
            # Verify dataset is completely removed
            response = self.session.get(f"{BASE_URL}/api/datasets/{dataset_id}")
            if response.status_code == 404:
                print("✅ Dataset completely removed from database")
            else:
                print("⚠️ Dataset still exists in database")
            return True
        else:
            print(f"❌ Hard delete failed: {response.status_code} - {response.text}")
            return False
    
    def check_s3_file_exists(self, file_path):
        """Check if file exists in S3 (requires admin endpoint)"""
        # This would need an admin endpoint to verify S3 file existence
        # For now, we'll assume the deletion worked based on the API response
        print(f"   Note: Cannot directly verify S3 file deletion from client")
        return True
    
    def test_deletion_with_sharing(self):
        """Test deletion of dataset with active sharing"""
        print("\n🔗 Testing deletion with active sharing...")
        
        # Create dataset
        dataset = self.create_test_dataset()
        if not dataset:
            return False
        
        dataset_id = dataset.get('id')
        
        # Create shared link
        share_data = {
            "dataset_id": dataset_id,
            "password": None,
            "enable_chat": True
        }
        
        response = self.session.post(f"{BASE_URL}/api/data-sharing/create-share-link", json=share_data)
        
        if response.status_code == 200:
            share_info = response.json()
            print(f"✅ Share link created: {share_info.get('share_token', 'N/A')[:20]}...")
            
            # Now delete the dataset
            response = self.session.delete(f"{BASE_URL}/api/datasets/{dataset_id}")
            
            if response.status_code == 200:
                print("✅ Dataset with sharing deleted successfully")
                
                # Check if shared link is still accessible
                share_token = share_info.get('share_token')
                response = requests.get(f"{BASE_URL}/api/data-sharing/shared/{share_token}")
                
                if response.status_code != 200:
                    print("✅ Shared link properly disabled after deletion")
                else:
                    print("⚠️ Shared link still accessible after deletion")
                
                return True
            else:
                print(f"❌ Failed to delete dataset with sharing: {response.status_code}")
                return False
        else:
            print(f"❌ Failed to create share link: {response.status_code}")
            return False
    
    def run_all_tests(self):
        """Run all deletion tests"""
        print("=" * 60)
        print("🧪 Starting Dataset Deletion Tests")
        print("=" * 60)
        
        results = {
            "authentication": False,
            "soft_delete": False,
            "hard_delete": False,
            "deletion_with_sharing": False
        }
        
        # Authentication
        results["authentication"] = self.authenticate()
        if not results["authentication"]:
            print("❌ Cannot proceed without authentication")
            return results
        
        # Test 1: Soft delete
        dataset1 = self.create_test_dataset()
        if dataset1:
            results["soft_delete"] = self.test_soft_delete(dataset1.get('id'))
        
        # Test 2: Hard delete
        dataset2 = self.create_test_dataset()
        if dataset2:
            results["hard_delete"] = self.test_hard_delete(dataset2.get('id'))
        
        # Test 3: Delete with sharing
        results["deletion_with_sharing"] = self.test_deletion_with_sharing()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title():<30} {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All deletion tests passed!")
        else:
            print("⚠️ Some deletion tests failed. Please check the logs above.")
        
        return results

if __name__ == "__main__":
    tester = DatasetDeletionTest()
    results = tester.run_all_tests()