#!/usr/bin/env python3
"""
Comprehensive AI Share Platform Test Suite with Data Connections
Tests complete system functionality including the new data connections feature
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class AISharePlatformTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_users = []
        self.test_orgs = []
        self.test_datasets = []
        self.test_connectors = []
        self.results = {
            "passed": 0,
            "failed": 0,
            "tests": []
        }

    def log_test(self, name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if details:
            print(f"    Details: {details}")
        
        self.results["tests"].append({
            "name": name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        if passed:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1

    def test_backend_health(self):
        """Test backend health endpoints"""
        print("\n🔍 Testing Backend Health...")
        
        try:
            # Test root endpoint
            response = self.session.get(f"{BASE_URL}/")
            self.log_test(
                "Backend Root Endpoint",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            # Test health endpoint
            response = self.session.get(f"{BASE_URL}/health")
            self.log_test(
                "Backend Health Check",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            if response.status_code == 200:
                health_data = response.json()
                mindsdb_status = health_data.get("services", {}).get("mindsdb", {}).get("status")
                self.log_test(
                    "MindsDB Service Health",
                    mindsdb_status == "available",
                    f"MindsDB Status: {mindsdb_status}"
                )
                
        except Exception as e:
            self.log_test("Backend Health", False, f"Error: {str(e)}")

    def test_user_registration_and_auth(self):
        """Test user registration and authentication"""
        print("\n👥 Testing User Registration and Authentication...")
        
        # Test user data
        test_users_data = [
            {
                "email": f"testuser1_{int(time.time())}@example.com",
                "password": "testpass123",
                "full_name": "Test User One",
                "create_organization": True,
                "organization_name": f"Test Org Alpha {int(time.time())}"
            },
            {
                "email": f"testuser2_{int(time.time())}@example.com", 
                "password": "testpass123",
                "full_name": "Test User Two",
                "create_organization": True,
                "organization_name": f"Test Org Beta {int(time.time())}"
            }
        ]
        
        for i, user_data in enumerate(test_users_data):
            try:
                # Register user
                response = self.session.post(f"{BASE_URL}/api/auth/register", json=user_data)
                self.log_test(
                    f"User Registration {i+1}",
                    response.status_code in [200, 201],
                    f"Status: {response.status_code}"
                )
                
                if response.status_code in [200, 201]:
                    user_info = response.json()
                    self.test_users.append({
                        "email": user_data["email"],
                        "password": user_data["password"],
                        "user_info": user_info
                    })
                    
                    # Test login
                    login_data = {
                        "username": user_data["email"],
                        "password": user_data["password"]
                    }
                    response = self.session.post(
                        f"{BASE_URL}/api/auth/login",
                        data=login_data,
                        headers={'Content-Type': 'application/x-www-form-urlencoded'}
                    )
                    
                    self.log_test(
                        f"User Login {i+1}",
                        response.status_code == 200,
                        f"Status: {response.status_code}"
                    )
                    
                    if response.status_code == 200:
                        auth_data = response.json()
                        token = auth_data.get("access_token")
                        if token:
                            self.test_users[i]["token"] = token
                            if i == 0:  # Use first user as primary
                                self.auth_token = token
                                self.session.headers.update({"Authorization": f"Bearer {token}"})
                                
            except Exception as e:
                self.log_test(f"User Registration/Login {i+1}", False, f"Error: {str(e)}")

    def test_data_connectors(self):
        """Test data connectors functionality"""
        print("\n🔗 Testing Data Connectors...")
        
        if not self.auth_token:
            self.log_test("Data Connectors Test", False, "No authentication token available")
            return
            
        # Test connector configurations
        test_connectors = [
            {
                "name": f"MySQL Test Connection {int(time.time())}",
                "connector_type": "mysql",
                "description": "Test MySQL database connection",
                "connection_config": {
                    "host": "localhost",
                    "port": 3306,
                    "database": "testdb"
                },
                "credentials": {
                    "user": "testuser",
                    "password": "testpass"
                }
            },
            {
                "name": f"PostgreSQL Test Connection {int(time.time())}",
                "connector_type": "postgresql", 
                "description": "Test PostgreSQL database connection",
                "connection_config": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "testdb"
                },
                "credentials": {
                    "user": "testuser",
                    "password": "testpass"
                }
            },
            {
                "name": f"S3 Test Connection {int(time.time())}",
                "connector_type": "s3",
                "description": "Test S3 bucket connection",
                "connection_config": {
                    "bucket": "test-bucket",
                    "region": "us-east-1"
                },
                "credentials": {
                    "aws_access_key_id": "test_access_key",
                    "aws_secret_access_key": "test_secret_key"
                }
            }
        ]
        
        # Test creating connectors
        for i, connector_data in enumerate(test_connectors):
            try:
                response = self.session.post(f"{BASE_URL}/api/connectors", json=connector_data)
                self.log_test(
                    f"Create {connector_data['connector_type'].upper()} Connector",
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )
                
                if response.status_code == 200:
                    connector_info = response.json()
                    self.test_connectors.append(connector_info)
                    
            except Exception as e:
                self.log_test(f"Create {connector_data['connector_type'].upper()} Connector", False, f"Error: {str(e)}")
        
        # Test listing connectors
        try:
            response = self.session.get(f"{BASE_URL}/api/connectors")
            self.log_test(
                "List Data Connectors",
                response.status_code == 200,
                f"Status: {response.status_code}, Count: {len(response.json()) if response.status_code == 200 else 0}"
            )
        except Exception as e:
            self.log_test("List Data Connectors", False, f"Error: {str(e)}")
            
        # Test getting specific connector
        if self.test_connectors:
            try:
                connector_id = self.test_connectors[0]["id"]
                response = self.session.get(f"{BASE_URL}/api/connectors/{connector_id}")
                self.log_test(
                    "Get Specific Connector",
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )
            except Exception as e:
                self.log_test("Get Specific Connector", False, f"Error: {str(e)}")
        
        # Test connector connection testing (will likely fail for test credentials, but endpoint should work)
        if self.test_connectors:
            try:
                connector_id = self.test_connectors[0]["id"]
                response = self.session.post(f"{BASE_URL}/api/connectors/{connector_id}/test")
                self.log_test(
                    "Test Connector Connection",
                    response.status_code in [200, 400],  # 400 is ok for test credentials
                    f"Status: {response.status_code}"
                )
            except Exception as e:
                self.log_test("Test Connector Connection", False, f"Error: {str(e)}")

    def test_dataset_operations(self):
        """Test dataset upload and management"""
        print("\n📊 Testing Dataset Operations...")
        
        if not self.auth_token:
            self.log_test("Dataset Operations", False, "No authentication token available")
            return
            
        # Create test CSV content
        csv_content = """name,age,city,salary
John Doe,30,New York,75000
Jane Smith,25,Los Angeles,68000
Bob Johnson,35,Chicago,82000
Alice Brown,28,Houston,71000
Charlie Wilson,32,Phoenix,77000"""
        
        # Test file upload
        try:
            files = {"file": ("test_data.csv", csv_content, "text/csv")}
            data = {
                "name": f"Test Dataset {int(time.time())}",
                "description": "Test dataset for connection integration",
                "sharing_level": "organization"
            }
            
            response = self.session.post(f"{BASE_URL}/api/datasets/upload", files=files, data=data)
            self.log_test(
                "Dataset Upload",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            if response.status_code == 200:
                dataset_info = response.json()
                self.test_datasets.append(dataset_info)
                
        except Exception as e:
            self.log_test("Dataset Upload", False, f"Error: {str(e)}")
            
        # Test dataset listing
        try:
            response = self.session.get(f"{BASE_URL}/api/datasets")
            self.log_test(
                "List Datasets",
                response.status_code == 200,
                f"Status: {response.status_code}, Count: {len(response.json()) if response.status_code == 200 else 0}"
            )
        except Exception as e:
            self.log_test("List Datasets", False, f"Error: {str(e)}")

    def test_ai_chat_functionality(self):
        """Test AI chat with datasets"""
        print("\n🤖 Testing AI Chat Functionality...")
        
        if not self.test_datasets:
            self.log_test("AI Chat Test", False, "No test datasets available")
            return
            
        dataset = self.test_datasets[0]
        dataset_id = dataset.get("id")
        
        if not dataset_id:
            self.log_test("AI Chat Test", False, "Invalid dataset ID")
            return
            
        # Test AI chat
        try:
            chat_data = {
                "message": "What insights can you provide about this dataset?",
                "dataset_id": dataset_id
            }
            
            response = self.session.post(f"{BASE_URL}/api/datasets/{dataset_id}/chat", json=chat_data)
            self.log_test(
                "AI Chat with Dataset",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            if response.status_code == 200:
                chat_response = response.json()
                ai_response = chat_response.get("response", "")
                self.log_test(
                    "AI Response Quality",
                    len(ai_response) > 50,
                    f"Response length: {len(ai_response)} characters"
                )
                
        except Exception as e:
            self.log_test("AI Chat with Dataset", False, f"Error: {str(e)}")

    def test_mindsdb_integration(self):
        """Test MindsDB integration and status"""
        print("\n🧠 Testing MindsDB Integration...")
        
        try:
            # Test MindsDB status
            response = self.session.get(f"{BASE_URL}/api/mindsdb/status")
            self.log_test(
                "MindsDB Status Check",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            # Test MindsDB databases
            response = self.session.get(f"{BASE_URL}/api/mindsdb/databases")
            self.log_test(
                "MindsDB Databases",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("MindsDB Integration", False, f"Error: {str(e)}")

    def test_frontend_connectivity(self):
        """Test frontend connectivity"""
        print("\n🌐 Testing Frontend Connectivity...")
        
        try:
            response = requests.get(FRONTEND_URL, timeout=10)
            self.log_test(
                "Frontend Accessibility",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test("Frontend Accessibility", False, f"Error: {str(e)}")

    def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete test connectors
        for connector in self.test_connectors:
            try:
                response = self.session.delete(f"{BASE_URL}/api/connectors/{connector['id']}")
                self.log_test(
                    f"Delete Connector {connector['id']}",
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )
            except Exception as e:
                self.log_test(f"Delete Connector {connector['id']}", False, f"Error: {str(e)}")
        
        # Delete test datasets  
        for dataset in self.test_datasets:
            try:
                dataset_id = dataset.get('id')
                if dataset_id:
                    response = self.session.delete(f"{BASE_URL}/api/datasets/{dataset_id}")
                    self.log_test(
                        f"Delete Dataset {dataset_id}",
                        response.status_code == 200,
                        f"Status: {response.status_code}"
                    )
            except Exception as e:
                self.log_test(f"Delete Dataset {dataset.get('id', 'unknown')}", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting Comprehensive AI Share Platform Test Suite")
        print(f"⏰ Test started at: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Run all tests
        self.test_backend_health()
        self.test_user_registration_and_auth()
        self.test_data_connectors()  # New test for data connectors
        self.test_dataset_operations()
        self.test_ai_chat_functionality()
        self.test_mindsdb_integration()
        self.test_frontend_connectivity()
        
        # Cleanup
        self.cleanup()
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📈 Success Rate: {(self.results['passed'] / (self.results['passed'] + self.results['failed']) * 100):.1f}%")
        
        # Print failed tests
        failed_tests = [test for test in self.results['tests'] if not test['passed']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['name']}: {test['details']}")
        
        print(f"\n⏰ Test completed at: {datetime.now().isoformat()}")
        
        # Save detailed results
        results_file = f"test_results/complete_system_test_{int(time.time())}.json"
        os.makedirs("test_results", exist_ok=True)
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"📄 Detailed results saved to: {results_file}")
        
        return self.results['failed'] == 0

def main():
    """Main test execution"""
    tester = AISharePlatformTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! The AI Share Platform with Data Connections is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main() 