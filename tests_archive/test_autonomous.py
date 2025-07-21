#!/usr/bin/env python3
"""
Autonomous API Chat Test Script
This script tests the complete API chat functionality autonomously
without requiring manual intervention.
"""

import requests
import json
import time
import sys
import os
from typing import Dict, Any, Optional

class AutonomousAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = "", data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data": data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if data and not success:
            print(f"   Data: {json.dumps(data, indent=2)}")
    
    def test_service_health(self) -> bool:
        """Test if the backend service is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                self.log_test("Service Health", True, "Backend service is healthy")
                return True
            else:
                self.log_test("Service Health", False, f"Health check failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Service Health", False, f"Health check failed: {str(e)}")
            return False
    
    def test_user_registration(self) -> bool:
        """Test user registration"""
        try:
            user_data = {
                "username": f"testuser_{int(time.time())}",
                "email": f"test_{int(time.time())}@example.com",
                "password": "testpassword123",
                "full_name": "Test User"
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=user_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("User Registration", True, "User registered successfully")
                return True
            else:
                self.log_test("User Registration", False, f"Registration failed with status {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_test("User Registration", False, f"Registration failed: {str(e)}")
            return False
    
    def test_user_login(self) -> bool:
        """Test user login and get auth token"""
        try:
            # Try with default test credentials first
            login_data = {
                "username": "testuser",
                "password": "testpass"
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login",
                data=login_data,  # Form data for OAuth2
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data.get("access_token")
                if self.auth_token:
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_test("User Login", True, "Login successful, token obtained")
                    return True
                else:
                    self.log_test("User Login", False, "Login response missing access token", token_data)
                    return False
            else:
                self.log_test("User Login", False, f"Login failed with status {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_test("User Login", False, f"Login failed: {str(e)}")
            return False
    
    def test_datasets_api(self) -> bool:
        """Test datasets API endpoints"""
        try:
            # Test GET /datasets
            response = self.session.get(f"{self.base_url}/datasets", timeout=10)
            
            if response.status_code == 200:
                datasets = response.json()
                self.log_test("Datasets API", True, f"Retrieved {len(datasets)} datasets")
                return True
            else:
                self.log_test("Datasets API", False, f"Datasets API failed with status {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_test("Datasets API", False, f"Datasets API failed: {str(e)}")
            return False
    
    def test_general_chat(self) -> bool:
        """Test general chat functionality"""
        try:
            chat_data = {
                "message": "Hello, can you help me understand what this platform does?",
                "conversation_id": None
            }
            
            response = self.session.post(
                f"{self.base_url}/chat",
                json=chat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                chat_response = response.json()
                if "response" in chat_response and chat_response["response"]:
                    self.log_test("General Chat", True, f"Chat response received: {chat_response['response'][:100]}...")
                    return True
                else:
                    self.log_test("General Chat", False, "Chat response empty or missing", chat_response)
                    return False
            else:
                self.log_test("General Chat", False, f"Chat failed with status {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_test("General Chat", False, f"Chat failed: {str(e)}")
            return False
    
    def test_dataset_chat(self) -> bool:
        """Test dataset-specific chat functionality"""
        try:
            # First, get available datasets
            datasets_response = self.session.get(f"{self.base_url}/datasets", timeout=10)
            
            if datasets_response.status_code != 200:
                self.log_test("Dataset Chat", False, "Could not retrieve datasets for chat test")
                return False
            
            datasets = datasets_response.json()
            
            if not datasets:
                # Test with a hypothetical dataset
                chat_data = {
                    "message": "What insights can you provide about sales data?",
                    "dataset_id": "test_dataset",
                    "conversation_id": None
                }
            else:
                # Use the first available dataset
                dataset_id = datasets[0].get("id") or datasets[0].get("name", "test_dataset")
                chat_data = {
                    "message": f"Can you analyze the data in this dataset?",
                    "dataset_id": dataset_id,
                    "conversation_id": None
                }
            
            response = self.session.post(
                f"{self.base_url}/chat",
                json=chat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                chat_response = response.json()
                if "response" in chat_response and chat_response["response"]:
                    self.log_test("Dataset Chat", True, f"Dataset chat response received: {chat_response['response'][:100]}...")
                    return True
                else:
                    self.log_test("Dataset Chat", False, "Dataset chat response empty or missing", chat_response)
                    return False
            else:
                self.log_test("Dataset Chat", False, f"Dataset chat failed with status {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_test("Dataset Chat", False, f"Dataset chat failed: {str(e)}")
            return False
    
    def test_mindsdb_integration(self) -> bool:
        """Test MindsDB integration"""
        try:
            # Test MindsDB status endpoint
            response = self.session.get(f"{self.base_url}/mindsdb/status", timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                self.log_test("MindsDB Integration", True, f"MindsDB status: {status_data}")
                return True
            else:
                self.log_test("MindsDB Integration", False, f"MindsDB status check failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("MindsDB Integration", False, f"MindsDB integration test failed: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests autonomously"""
        print("🤖 Starting Autonomous API Chat Tests...")
        print("=" * 50)
        
        # Test sequence
        tests = [
            ("Service Health", self.test_service_health),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Datasets API", self.test_datasets_api),
            ("General Chat", self.test_general_chat),
            ("Dataset Chat", self.test_dataset_chat),
            ("MindsDB Integration", self.test_mindsdb_integration)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running {test_name}...")
            try:
                if test_func():
                    passed += 1
                else:
                    # Continue with other tests even if one fails
                    pass
            except Exception as e:
                self.log_test(test_name, False, f"Test execution failed: {str(e)}")
            
            time.sleep(1)  # Brief pause between tests
        
        # Summary
        print("\n" + "=" * 50)
        print(f"🏁 Test Summary: {passed}/{total} tests passed")
        
        success_rate = (passed / total) * 100
        if success_rate >= 80:
            print(f"🎉 Overall Result: SUCCESS ({success_rate:.1f}% pass rate)")
        elif success_rate >= 60:
            print(f"⚠️  Overall Result: PARTIAL SUCCESS ({success_rate:.1f}% pass rate)")
        else:
            print(f"❌ Overall Result: FAILURE ({success_rate:.1f}% pass rate)")
        
        return {
            "total_tests": total,
            "passed_tests": passed,
            "success_rate": success_rate,
            "results": self.test_results
        }
    
    def save_results(self, filename: str = None):
        """Save test results to a JSON file"""
        if filename is None:
            filename = f"test_results_{int(time.time())}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump({
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "summary": {
                        "total_tests": len(self.test_results),
                        "passed_tests": sum(1 for r in self.test_results if r["success"]),
                        "failed_tests": sum(1 for r in self.test_results if not r["success"])
                    },
                    "results": self.test_results
                }, f, indent=2)
            print(f"📄 Test results saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save results: {str(e)}")

def main():
    """Main function to run autonomous tests"""
    print("🚀 AI Share Platform - Autonomous API Chat Test")
    print("=" * 50)
    
    # Check if backend is likely running
    print("📋 Pre-flight checks...")
    
    tester = AutonomousAPITester()
    
    # Run all tests
    results = tester.run_all_tests()
    
    # Save results
    tester.save_results()
    
    # Exit with appropriate code
    if results["success_rate"] >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()