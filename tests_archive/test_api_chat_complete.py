#!/usr/bin/env python3
"""
Comprehensive API Chat Functionality Test
Tests the complete chat workflow including authentication, dataset management, and chat API.
"""

import requests
import json
import time
import sys
from typing import Dict, Any

class APITester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.mindsdb_url = "http://localhost:47334"
        self.session = requests.Session()
        self.auth_token = None
        
    def test_service_health(self) -> bool:
        """Test if all services are running"""
        print("🏥 Testing service health...")
        
        # Test backend
        try:
            response = self.session.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend is healthy")
            else:
                print(f"❌ Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend connection failed: {e}")
            return False
            
        # Test frontend
        try:
            response = self.session.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                print("✅ Frontend is accessible")
            else:
                print(f"❌ Frontend accessibility failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Frontend connection failed: {e}")
            return False
            
        # Test MindsDB
        try:
            response = self.session.get(f"{self.mindsdb_url}/api/status", timeout=5)
            if response.status_code == 200:
                print("✅ MindsDB is accessible")
            else:
                print(f"⚠️  MindsDB status check returned: {response.status_code}")
        except Exception as e:
            print(f"⚠️  MindsDB connection failed: {e} (this might be expected)")
            
        return True
        
    def test_authentication(self) -> bool:
        """Test user authentication"""
        print("\n🔐 Testing authentication...")
        
        # Test login
        login_data = {
            "username": "admin@example.com",
            "password": "admin123"
        }
        
        try:
            response = self.session.post(
                f"{self.backend_url}/api/auth/login",
                data=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.auth_token = result.get("access_token")
                if self.auth_token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    print("✅ Authentication successful")
                    return True
                else:
                    print("❌ No access token in response")
                    return False
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
            
    def test_datasets_api(self) -> bool:
        """Test datasets API endpoints"""
        print("\n📊 Testing datasets API...")
        
        try:
            # Test get datasets
            response = self.session.get(f"{self.backend_url}/api/datasets", timeout=10)
            
            if response.status_code == 200:
                datasets = response.json()
                print(f"✅ Datasets API working - Found {len(datasets)} datasets")
                
                # Print some dataset info if available
                if datasets:
                    for i, dataset in enumerate(datasets[:3]):  # Show first 3
                        print(f"   Dataset {i+1}: {dataset.get('name', 'Unknown')} - {dataset.get('description', 'No description')[:50]}...")
                        
                return True
            else:
                print(f"❌ Datasets API failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Datasets API error: {e}")
            return False
            
    def test_chat_api(self) -> bool:
        """Test chat API endpoints"""
        print("\n💬 Testing chat API...")
        
        try:
            # Test chat endpoint with a simple message
            chat_data = {
                "message": "Hello, can you help me analyze some data?",
                "dataset_id": None  # Test without specific dataset first
            }
            
            response = self.session.post(
                f"{self.backend_url}/api/chat",
                json=chat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Chat API working")
                print(f"   Response: {result.get('response', 'No response')[:100]}...")
                return True
            else:
                print(f"❌ Chat API failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Chat API error: {e}")
            return False
            
    def test_chat_with_dataset(self) -> bool:
        """Test chat API with a specific dataset"""
        print("\n📈 Testing chat with dataset...")
        
        try:
            # First get available datasets
            response = self.session.get(f"{self.backend_url}/api/datasets", timeout=10)
            
            if response.status_code != 200:
                print("❌ Could not fetch datasets for chat test")
                return False
                
            datasets = response.json()
            if not datasets:
                print("⚠️  No datasets available for chat test")
                return True  # Not a failure, just no data to test with
                
            # Use the first dataset for testing
            dataset_id = datasets[0].get('id')
            dataset_name = datasets[0].get('name', 'Unknown')
            
            chat_data = {
                "message": f"Can you tell me about the {dataset_name} dataset?",
                "dataset_id": dataset_id
            }
            
            response = self.session.post(
                f"{self.backend_url}/api/chat",
                json=chat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Chat with dataset '{dataset_name}' working")
                print(f"   Response: {result.get('response', 'No response')[:100]}...")
                return True
            else:
                print(f"❌ Chat with dataset failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Chat with dataset error: {e}")
            return False
            
    def run_all_tests(self) -> bool:
        """Run all tests and return overall success"""
        print("🚀 Starting comprehensive API chat functionality tests...\n")
        
        tests = [
            ("Service Health", self.test_service_health),
            ("Authentication", self.test_authentication),
            ("Datasets API", self.test_datasets_api),
            ("Chat API", self.test_chat_api),
            ("Chat with Dataset", self.test_chat_with_dataset)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
                if not result:
                    print(f"\n❌ {test_name} test failed - stopping here")
                    break
            except Exception as e:
                print(f"\n💥 {test_name} test crashed: {e}")
                results.append((test_name, False))
                break
                
        # Print summary
        print("\n" + "="*50)
        print("📋 TEST SUMMARY")
        print("="*50)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
            if result:
                passed += 1
                
        print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
        
        if passed == len(results):
            print("🎉 All API chat functionality tests PASSED!")
            return True
        else:
            print("⚠️  Some tests failed - check the logs above")
            return False

if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)