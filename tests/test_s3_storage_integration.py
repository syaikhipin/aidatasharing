#!/usr/bin/env python3
"""
Test script for S3 storage integration, file upload/download, and MindsDB chat functionality.
"""

import requests
import json
import os
import tempfile
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "alice@techcorp.com"
TEST_PASSWORD = "Password123!"

class S3StorageTest:
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
    
    def create_test_file(self, filename="test_data.csv", content=None):
        """Create a temporary test file"""
        if content is None:
            content = """name,age,city
Alice,25,New York
Bob,30,San Francisco
Charlie,35,Chicago
Diana,28,Seattle
"""
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=f'.{filename.split(".")[-1]}', delete=False)
        temp_file.write(content)
        temp_file.close()
        
        return temp_file.name
    
    def test_file_upload(self):
        """Test file upload functionality with S3 storage"""
        print("\n📁 Testing file upload to S3...")
        
        # Create test file
        test_file_path = self.create_test_file()
        
        try:
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test_data.csv', f, 'text/csv')}
                data = {
                    'title': 'S3 Test Dataset',
                    'description': 'Test dataset for S3 storage functionality',
                    'tags': 'test,s3,storage'
                }
                
                response = self.session.post(f"{BASE_URL}/api/datasets/upload", files=files, data=data)
                
                if response.status_code == 200:
                    response_data = response.json()
                    print(f"✅ File uploaded successfully to S3")
                    
                    # Extract dataset from response
                    if 'dataset' in response_data:
                        dataset_data = response_data['dataset']
                    elif isinstance(response_data, list) and len(response_data) > 0:
                        dataset_data = response_data[0]  # Take first dataset if list
                    else:
                        dataset_data = response_data
                    
                    print(f"   Dataset ID: {dataset_data.get('id', 'N/A')}")
                    print(f"   Storage Path: {dataset_data.get('file_path', 'N/A')}")
                    print(f"   Source URL: {dataset_data.get('source_url', 'N/A')}")
                    return dataset_data
                else:
                    print(f"❌ File upload failed: {response.status_code} - {response.text}")
                    return None
        
        finally:
            # Clean up test file
            os.unlink(test_file_path)
    
    def test_file_download(self, dataset_id):
        """Test file download functionality from S3"""
        print(f"\n⬇️ Testing file download from S3...")
        
        # Step 1: Get download token
        response = self.session.get(f"{BASE_URL}/api/datasets/{dataset_id}/download")
        
        if response.status_code != 200:
            print(f"❌ Failed to get download token: {response.status_code} - {response.text}")
            return False
            
        download_info = response.json()
        download_token = download_info.get('download_token')
        
        if not download_token:
            print(f"❌ No download token in response")
            return False
            
        print(f"   Download Token: {download_token[:20]}...")
        
        # Step 2: Execute download using token
        response = self.session.get(f"{BASE_URL}/api/datasets/download/{download_token}")
        
        if response.status_code == 200:
            print("✅ File downloaded successfully from S3")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"   Content-Length: {len(response.content)} bytes")
            
            # Verify content
            if response.content:
                try:
                    content = response.content.decode('utf-8')
                    if 'Alice' in content and 'Bob' in content:
                        print("✅ Downloaded content verified")
                        return True
                    else:
                        print("❌ Downloaded content verification failed")
                        return False
                except:
                    # If it's not text, just check if we got content
                    if len(response.content) > 0:
                        print("✅ Downloaded binary content verified")
                        return True
                    else:
                        print("❌ Empty content received")
                        return False
            return True
        else:
            print(f"❌ File download failed: {response.status_code} - {response.text}")
            return False
    
    def create_shared_link(self, dataset_id):
        """Create a shared link for the dataset"""
        print(f"\n🔗 Creating shared link...")
        
        share_data = {
            "dataset_id": dataset_id,
            "password": None,
            "enable_chat": True
        }
        
        response = self.session.post(f"{BASE_URL}/api/data-sharing/create-share-link", json=share_data)
        
        if response.status_code == 200:
            share_data = response.json()
            print(f"✅ Shared link created successfully")
            print(f"   Share Token: {share_data['share_token']}")
            return share_data['share_token']
        else:
            print(f"❌ Shared link creation failed: {response.status_code} - {response.text}")
            return None
    
    def test_mindsdb_chat_shared(self, share_token):
        """Test MindsDB chat functionality on shared page"""
        print(f"\n💬 Testing MindsDB chat on shared page...")
        
        # First, get shared dataset info without authentication
        response = requests.get(f"{BASE_URL}/api/data-sharing/shared/{share_token}")
        
        if response.status_code != 200:
            print(f"❌ Failed to access shared page: {response.status_code} - {response.text}")
            return False
        
        shared_data = response.json()
        
        # Extract dataset ID from response (handle different formats)
        if 'dataset_id' in shared_data:
            dataset_id = shared_data['dataset_id']
        elif 'dataset' in shared_data and 'id' in shared_data['dataset']:
            dataset_id = shared_data['dataset']['id']
        else:
            print(f"❌ No dataset ID found in shared data")
            return False
        
        # Test chat on shared page using the public endpoint
        chat_data = {
            "message": "What can you tell me about this dataset? How many rows does it have?"
        }
        
        # Use the public shared chat endpoint
        response = requests.post(f"{BASE_URL}/api/data-sharing/public/shared/{share_token}/chat", json=chat_data)
        
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ MindsDB chat on shared page successful")
            print(f"   Response: {chat_response.get('response', 'N/A')[:200]}...")
            return True
        else:
            print(f"❌ MindsDB chat on shared page failed: {response.status_code} - {response.text}")
            return False
    
    def test_mindsdb_chat_authenticated(self, dataset_id):
        """Test MindsDB chat functionality on authenticated page"""
        print(f"\n💬 Testing MindsDB chat on authenticated page...")
        
        chat_data = {
            "message": "Can you analyze the age distribution in this dataset and provide insights?"
        }
        
        response = self.session.post(f"{BASE_URL}/api/datasets/{dataset_id}/chat", json=chat_data)
        
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ MindsDB chat on authenticated page successful")
            print(f"   Response: {chat_response.get('response', 'N/A')[:200]}...")
            return True
        else:
            print(f"❌ MindsDB chat on authenticated page failed: {response.status_code} - {response.text}")
            return False
    
    def test_health_check(self):
        """Test API health check"""
        print("🏥 Testing API health check...")
        
        response = requests.get(f"{BASE_URL}/health")
        
        if response.status_code == 200:
            health_data = response.json()
            print("✅ API health check passed")
            print(f"   Status: {health_data.get('status', 'N/A')}")
            print(f"   Storage Type: {health_data.get('storage_type', 'N/A')}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code} - {response.text}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("🧪 Starting S3 Storage Integration Tests")
        print("=" * 60)
        
        results = {
            "health_check": False,
            "authentication": False,
            "file_upload": False,
            "file_download": False,
            "shared_link": False,
            "mindsdb_chat_shared": False,
            "mindsdb_chat_authenticated": False
        }
        
        # Health check
        results["health_check"] = self.test_health_check()
        
        # Authentication
        results["authentication"] = self.authenticate()
        if not results["authentication"]:
            print("❌ Cannot proceed without authentication")
            return results
        
        # File upload
        dataset_data = self.test_file_upload()
        if dataset_data:
            results["file_upload"] = True
            dataset_id = dataset_data.get('id')
            if not dataset_id:
                print("❌ No dataset ID in response, cannot proceed with other tests")
                return results
            
            # File download
            results["file_download"] = self.test_file_download(dataset_id)
            
            # Create shared link
            share_token = self.create_shared_link(dataset_id)
            if share_token:
                results["shared_link"] = True
                
                # Test MindsDB chat on shared page
                time.sleep(2)  # Give some time for processing
                results["mindsdb_chat_shared"] = self.test_mindsdb_chat_shared(share_token)
            
            # Test MindsDB chat on authenticated page
            time.sleep(2)  # Give some time for processing
            results["mindsdb_chat_authenticated"] = self.test_mindsdb_chat_authenticated(dataset_id)
        
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
            print("🎉 All tests passed! S3 storage integration is working correctly.")
        else:
            print("⚠️ Some tests failed. Please check the logs above.")
        
        return results

if __name__ == "__main__":
    tester = S3StorageTest()
    results = tester.run_all_tests()