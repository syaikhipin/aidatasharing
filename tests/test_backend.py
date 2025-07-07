"""
Comprehensive Backend Test Suite for AI Share Platform
Tests all API endpoints, authentication, database operations, and integrations
"""

import pytest
import requests
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class BackendTestSuite:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_user_id = None
        self.test_org_id = None
        self.test_dataset_id = None
        self.test_model_id = None
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all backend tests and return comprehensive results"""
        print("🧪 Starting Comprehensive Backend Test Suite")
        print("=" * 60)
        
        results = {
            "start_time": datetime.now().isoformat(),
            "tests": {},
            "summary": {},
            "errors": []
        }
        
        # Test categories
        test_categories = [
            ("Health Check", self.test_health_check),
            ("Authentication", self.test_authentication),
            ("Organization Management", self.test_organization_management),
            ("User Management", self.test_user_management),
            ("Dataset Operations", self.test_dataset_operations),
            ("Model Management", self.test_model_management),
            ("MindsDB Integration", self.test_mindsdb_integration),
            ("Analytics API", self.test_analytics_api),
            ("Data Access API", self.test_data_access_api),
            ("Security & Permissions", self.test_security_permissions),
            ("Error Handling", self.test_error_handling)
        ]
        
        for category_name, test_method in test_categories:
            print(f"\n📋 Testing: {category_name}")
            try:
                test_results = test_method()
                results["tests"][category_name] = test_results
                print(f"✅ {category_name}: {test_results['passed']}/{test_results['total']} tests passed")
            except Exception as e:
                results["errors"].append(f"{category_name}: {str(e)}")
                print(f"❌ {category_name}: Failed with error - {str(e)}")
        
        # Calculate summary
        total_tests = sum(r.get('total', 0) for r in results["tests"].values())
        passed_tests = sum(r.get('passed', 0) for r in results["tests"].values())
        
        results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "end_time": datetime.now().isoformat()
        }
        
        print(f"\n🎯 Backend Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Success Rate: {results['summary']['success_rate']:.1f}%")
        
        return results
    
    def test_health_check(self) -> Dict[str, Any]:
        """Test health check and basic server connectivity"""
        tests = []
        
        # Test 1: Basic health check
        try:
            response = self.session.get(f"{self.base_url}/health")
            tests.append({
                "name": "Health Check Endpoint",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Health Check Endpoint",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 2: API documentation
        try:
            response = self.session.get(f"{self.base_url}/docs")
            tests.append({
                "name": "API Documentation",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "API Documentation",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 3: OpenAPI schema
        try:
            response = self.session.get(f"{self.base_url}/openapi.json")
            tests.append({
                "name": "OpenAPI Schema",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "OpenAPI Schema",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_authentication(self) -> Dict[str, Any]:
        """Test authentication endpoints and JWT handling"""
        tests = []
        
        # Test 1: User registration
        try:
            register_data = {
                "email": f"testuser_{int(time.time())}@example.com",
                "password": "testpassword123",
                "full_name": f"Test User {int(time.time())}",
                "create_organization": True,
                "organization_name": f"Test Org {int(time.time())}"
            }
            
            response = self.session.post(f"{self.base_url}/api/auth/register", json=register_data)
            success = response.status_code == 201  # FastAPI returns 201 for successful registration
            if success and response.json():
                user_data = response.json()
                self.test_user_id = user_data.get("id")
                self.test_org_id = user_data.get("organization_id")
            
            tests.append({
                "name": "User Registration",
                "passed": success,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "User Registration",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 2: User login
        try:
            login_data = {
                "username": register_data["email"],  # OAuth2 expects username field
                "password": register_data["password"]
            }
            
            response = self.session.post(f"{self.base_url}/api/auth/login", data=login_data)
            success = response.status_code == 200
            if success and response.json():
                self.auth_token = response.json().get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            
            tests.append({
                "name": "User Login",
                "passed": success,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "User Login",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 3: Protected endpoint access
        try:
            response = self.session.get(f"{self.base_url}/api/auth/me")
            tests.append({
                "name": "Protected Endpoint Access",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Protected Endpoint Access",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 4: Invalid token handling
        try:
            invalid_session = requests.Session()
            invalid_session.headers.update({"Authorization": "Bearer invalid_token"})
            response = invalid_session.get(f"{self.base_url}/api/auth/me")
            tests.append({
                "name": "Invalid Token Handling",
                "passed": response.status_code == 401,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Invalid Token Handling",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_organization_management(self) -> Dict[str, Any]:
        """Test organization management endpoints"""
        tests = []
        
        # Test 1: Get organizations list
        try:
            response = self.session.get(f"{self.base_url}/api/organizations/")
            tests.append({
                "name": "Get Organizations List",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Get Organizations List",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 2: Get specific organization
        if self.test_org_id:
            try:
                response = self.session.get(f"{self.base_url}/api/organizations/{self.test_org_id}")
                tests.append({
                    "name": "Get Specific Organization",
                    "passed": response.status_code == 200,
                    "details": f"Status: {response.status_code}"
                })
            except Exception as e:
                tests.append({
                    "name": "Get Specific Organization",
                    "passed": False,
                    "details": f"Error: {str(e)}"
                })
        
        # Test 3: Create department
        if self.test_org_id:
            try:
                dept_data = {
                    "name": f"Test Department {int(time.time())}",
                    "description": "Test department for API testing"
                }
                response = self.session.post(
                    f"{self.base_url}/api/organizations/{self.test_org_id}/departments",
                    json=dept_data
                )
                tests.append({
                    "name": "Create Department",
                    "passed": response.status_code == 200,
                    "details": f"Status: {response.status_code}"
                })
            except Exception as e:
                tests.append({
                    "name": "Create Department",
                    "passed": False,
                    "details": f"Error: {str(e)}"
                })
        
        # Test 4: Get organization members
        if self.test_org_id:
            try:
                response = self.session.get(f"{self.base_url}/api/organizations/{self.test_org_id}/members")
                tests.append({
                    "name": "Get Organization Members",
                    "passed": response.status_code == 200,
                    "details": f"Status: {response.status_code}"
                })
            except Exception as e:
                tests.append({
                    "name": "Get Organization Members",
                    "passed": False,
                    "details": f"Error: {str(e)}"
                })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_dataset_operations(self) -> Dict[str, Any]:
        """Test dataset CRUD operations"""
        tests = []
        
        # Test 1: Get datasets list
        try:
            response = self.session.get(f"{self.base_url}/api/datasets/")
            tests.append({
                "name": "Get Datasets List",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Get Datasets List",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 2: Create dataset (mock upload)
        try:
            dataset_data = {
                "name": f"Test Dataset {int(time.time())}",
                "description": "Test dataset for API testing",
                "sharing_level": "PRIVATE",
                "data_format": "CSV",
                "columns": ["id", "name", "value"],
                "row_count": 100
            }
            
            response = self.session.post(f"{self.base_url}/api/datasets/", json=dataset_data)
            success = response.status_code == 201
            if success and response.json():
                self.test_dataset_id = response.json().get("id")
            
            tests.append({
                "name": "Create Dataset",
                "passed": success,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Create Dataset",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 3: Get specific dataset
        if self.test_dataset_id:
            try:
                response = self.session.get(f"{self.base_url}/api/datasets/{self.test_dataset_id}")
                tests.append({
                    "name": "Get Specific Dataset",
                    "passed": response.status_code == 200,
                    "details": f"Status: {response.status_code}"
                })
            except Exception as e:
                tests.append({
                    "name": "Get Specific Dataset",
                    "passed": False,
                    "details": f"Error: {str(e)}"
                })
        
        # Test 4: Update dataset
        if self.test_dataset_id:
            try:
                update_data = {
                    "description": "Updated test dataset description"
                }
                response = self.session.put(
                    f"{self.base_url}/api/datasets/{self.test_dataset_id}",
                    json=update_data
                )
                tests.append({
                    "name": "Update Dataset",
                    "passed": response.status_code == 200,
                    "details": f"Status: {response.status_code}"
                })
            except Exception as e:
                tests.append({
                    "name": "Update Dataset",
                    "passed": False,
                    "details": f"Error: {str(e)}"
                })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_model_management(self) -> Dict[str, Any]:
        """Test ML model management endpoints"""
        tests = []
        
        # Test 1: Get models list
        try:
            response = self.session.get(f"{self.base_url}/api/models/")
            tests.append({
                "name": "Get Models List",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Get Models List",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 2: Create model (if dataset exists)
        if self.test_dataset_id:
            try:
                model_data = {
                    "name": f"Test Model {int(time.time())}",
                    "dataset_id": self.test_dataset_id,
                    "target_column": "value",
                    "engine": "lightgbm",
                    "description": "Test model for API testing"
                }
                
                response = self.session.post(f"{self.base_url}/api/models/", json=model_data)
                success = response.status_code == 200
                if success and response.json():
                    self.test_model_id = response.json().get("id")
                
                tests.append({
                    "name": "Create Model",
                    "passed": success,
                    "details": f"Status: {response.status_code}"
                })
            except Exception as e:
                tests.append({
                    "name": "Create Model",
                    "passed": False,
                    "details": f"Error: {str(e)}"
                })
        
        # Test 3: Get specific model
        if self.test_model_id:
            try:
                response = self.session.get(f"{self.base_url}/api/models/{self.test_model_id}")
                tests.append({
                    "name": "Get Specific Model",
                    "passed": response.status_code == 200,
                    "details": f"Status: {response.status_code}"
                })
            except Exception as e:
                tests.append({
                    "name": "Get Specific Model",
                    "passed": False,
                    "details": f"Error: {str(e)}"
                })
        
        # Test 4: Model status check
        if self.test_model_id:
            try:
                response = self.session.get(f"{self.base_url}/api/models/{self.test_model_id}/status")
                tests.append({
                    "name": "Check Model Status",
                    "passed": response.status_code == 200,
                    "details": f"Status: {response.status_code}"
                })
            except Exception as e:
                tests.append({
                    "name": "Check Model Status",
                    "passed": False,
                    "details": f"Error: {str(e)}"
                })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_mindsdb_integration(self) -> Dict[str, Any]:
        """Test MindsDB integration endpoints"""
        tests = []
        
        # Test 1: MindsDB status
        try:
            response = self.session.get(f"{self.base_url}/api/mindsdb/status")
            tests.append({
                "name": "MindsDB Status Check",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "MindsDB Status Check",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 2: Execute query
        try:
            query_data = {
                "query": "SHOW DATABASES;"
            }
            response = self.session.post(f"{self.base_url}/api/mindsdb/query", json=query_data)
            tests.append({
                "name": "Execute MindsDB Query",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Execute MindsDB Query",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 3: AI query processing
        try:
            ai_query_data = {
                "query": "Show me all available data sources"
            }
            response = self.session.post(f"{self.base_url}/api/mindsdb/ai-query", json=ai_query_data)
            tests.append({
                "name": "AI Query Processing",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "AI Query Processing",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_analytics_api(self) -> Dict[str, Any]:
        """Test analytics API endpoints"""
        tests = []
        
        # Test 1: Organization analytics
        try:
            response = self.session.get(f"{self.base_url}/api/analytics/organization")
            tests.append({
                "name": "Organization Analytics",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Organization Analytics",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 2: Usage metrics (real-time endpoint)
        try:
            response = self.session.get(f"{self.base_url}/api/analytics/real-time")
            tests.append({
                "name": "Usage Metrics",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Usage Metrics",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 3: Export analytics
        try:
            response = self.session.get(f"{self.base_url}/api/analytics/export?format=json")
            tests.append({
                "name": "Export Analytics",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Export Analytics",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_data_access_api(self) -> Dict[str, Any]:
        """Test data access request API endpoints"""
        tests = []
        
        # Test 1: Get access requests
        try:
            response = self.session.get(f"{self.base_url}/api/data-access/requests")
            tests.append({
                "name": "Get Access Requests",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Get Access Requests",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 2: Create access request
        if self.test_dataset_id:
            try:
                request_data = {
                    "dataset_id": self.test_dataset_id,
                    "request_type": "access",
                    "requested_level": "read", 
                    "purpose": "Testing API access request functionality",
                    "justification": "Testing API access request functionality",
                    "category": "analysis",
                    "urgency": "low"
                }
                response = self.session.post(f"{self.base_url}/api/data-access/requests", json=request_data)
                # Status 400 is correct when user already has access to the dataset
                tests.append({
                    "name": "Create Access Request",
                    "passed": response.status_code in [200, 400],  # Both are valid
                    "details": f"Status: {response.status_code}"
                })
            except Exception as e:
                tests.append({
                    "name": "Create Access Request",
                    "passed": False,
                    "details": f"Error: {str(e)}"
                })
        
        # Test 3: Get audit trail
        try:
            response = self.session.get(f"{self.base_url}/api/data-access/audit")
            tests.append({
                "name": "Get Audit Trail",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Get Audit Trail",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_user_management(self) -> Dict[str, Any]:
        """Test user management endpoints"""
        tests = []
        
        # Test 1: Get current user profile
        try:
            response = self.session.get(f"{self.base_url}/api/auth/me")
            tests.append({
                "name": "Get User Profile",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Get User Profile",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 2: Update user profile
        try:
            update_data = {
                "username": f"updated_user_{int(time.time())}"
            }
            response = self.session.put(f"{self.base_url}/api/auth/me", json=update_data)
            tests.append({
                "name": "Update User Profile",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Update User Profile",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_security_permissions(self) -> Dict[str, Any]:
        """Test security and permission controls"""
        tests = []
        
        # Test 1: Access without authentication
        try:
            no_auth_session = requests.Session()
            response = no_auth_session.get(f"{self.base_url}/api/datasets/")
            tests.append({
                "name": "Unauthenticated Access Blocked",
                "passed": response.status_code == 403,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Unauthenticated Access Blocked",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 2: Invalid token
        try:
            invalid_session = requests.Session()
            invalid_session.headers.update({"Authorization": "Bearer invalid_token_12345"})
            response = invalid_session.get(f"{self.base_url}/api/datasets/")
            tests.append({
                "name": "Invalid Token Rejected",
                "passed": response.status_code == 401,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Invalid Token Rejected",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 3: CORS headers
        try:
            response = self.session.get(f"{self.base_url}/cors-test", headers={"Origin": "http://localhost:3000"})
            has_cors = "Access-Control-Allow-Origin" in response.headers
            tests.append({
                "name": "CORS Headers Present",
                "passed": has_cors,
                "details": f"CORS headers: {has_cors}"
            })
        except Exception as e:
            tests.append({
                "name": "CORS Headers Present",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and edge cases"""
        tests = []
        
        # Test 1: 404 for non-existent resource
        try:
            response = self.session.get(f"{self.base_url}/api/datasets/99999999")
            tests.append({
                "name": "404 for Non-existent Resource",
                "passed": response.status_code == 404,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "404 for Non-existent Resource",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 2: Invalid JSON data
        try:
            response = self.session.post(
                f"{self.base_url}/api/datasets/",
                data="invalid json data",
                headers={"Content-Type": "application/json"}
            )
            tests.append({
                "name": "Invalid JSON Handling",
                "passed": response.status_code == 422,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Invalid JSON Handling",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 3: Missing required fields
        try:
            response = self.session.post(f"{self.base_url}/api/datasets/", json={})
            tests.append({
                "name": "Missing Required Fields",
                "passed": response.status_code == 422,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": "Missing Required Fields",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }


def main():
    """Main function to run backend tests"""
    print("🚀 AI Share Platform - Backend Test Suite")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend server is not responding properly")
            print("Please start the backend server with: cd backend && python start.py")
            return
    except requests.exceptions.RequestException:
        print("❌ Backend server is not running or not accessible")
        print("Please start the backend server with: cd backend && python start.py")
        return
    
    # Run tests
    test_suite = BackendTestSuite()
    results = test_suite.run_all_tests()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"test_results/backend_test_results_{timestamp}.json"
    
    os.makedirs("test_results", exist_ok=True)
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Test results saved to: {results_file}")
    
    # Return success if all tests passed
    return results["summary"]["success_rate"] == 100.0


if __name__ == "__main__":
    main() 