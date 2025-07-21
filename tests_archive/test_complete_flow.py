#!/usr/bin/env python3
"""
Comprehensive test for AI Data Share Platform API integration
Tests the complete authentication flow and all major endpoints
"""

import requests
import json
import time
from typing import Dict, Any

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        
    def test_health_check(self) -> bool:
        """Test the health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            print(f"✓ Health check: {response.status_code} - {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"✗ Health check failed: {e}")
            return False
    
    def test_login(self, email: str = "admin@example.com", password: str = "admin123") -> bool:
        """Test user login and token retrieval"""
        try:
            login_data = {
                "username": email,
                "password": password
            }
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                print(f"✓ Login successful: Token obtained")
                return True
            else:
                print(f"✗ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"✗ Login failed: {e}")
            return False
    
    def test_protected_endpoints(self) -> Dict[str, bool]:
        """Test all protected endpoints"""
        endpoints = {
            "User Profile": "/api/auth/me",
            "Organizations": "/api/organizations/my",
            "Admin Stats": "/api/admin/stats",
            "Data Access Datasets": "/api/data-access/datasets",
            "Data Access Requests": "/api/data-access/requests",
            "Audit Logs": "/api/data-access/audit-logs",
            "MindsDB Status": "/api/mindsdb/status"
        }
        
        results = {}
        
        for name, endpoint in endpoints.items():
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                success = response.status_code == 200
                if success:
                    print(f"✓ {name}: {response.status_code} OK")
                else:
                    print(f"✗ {name}: {response.status_code} - {response.text[:100]}")
                results[name] = success
            except Exception as e:
                print(f"✗ {name}: Exception - {e}")
                results[name] = False
        
        return results
    
    def test_cors_preflight(self) -> bool:
        """Test CORS preflight requests"""
        try:
            response = self.session.options(
                f"{self.base_url}/api/auth/me",
                headers={
                    "Origin": "http://localhost:3004",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Authorization"
                }
            )
            success = response.status_code == 200
            if success:
                print(f"✓ CORS Preflight: {response.status_code} OK")
            else:
                print(f"✗ CORS Preflight: {response.status_code}")
            return success
        except Exception as e:
            print(f"✗ CORS Preflight failed: {e}")
            return False
    
    def test_data_operations(self) -> Dict[str, bool]:
        """Test data-related operations"""
        results = {}
        
        # Test creating a data access request
        try:
            request_data = {
                "dataset_id": 1,
                "purpose": "Testing API integration",
                "duration_days": 30
            }
            response = self.session.post(
                f"{self.base_url}/api/data-access/requests",
                json=request_data
            )
            success = response.status_code in [200, 201]
            if success:
                print(f"✓ Create Data Request: {response.status_code} OK")
            else:
                print(f"✗ Create Data Request: {response.status_code} - {response.text[:100]}")
            results["Create Data Request"] = success
        except Exception as e:
            print(f"✗ Create Data Request: Exception - {e}")
            results["Create Data Request"] = False
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        print("=" * 60)
        print("AI Data Share Platform - Comprehensive API Test")
        print("=" * 60)
        
        results = {
            "health_check": False,
            "login": False,
            "cors_preflight": False,
            "protected_endpoints": {},
            "data_operations": {},
            "overall_success": False
        }
        
        # Test health check
        print("\n1. Testing Health Check...")
        results["health_check"] = self.test_health_check()
        
        # Test login
        print("\n2. Testing Authentication...")
        results["login"] = self.test_login()
        
        if not results["login"]:
            print("\n❌ Cannot proceed without authentication")
            return results
        
        # Test CORS
        print("\n3. Testing CORS Configuration...")
        results["cors_preflight"] = self.test_cors_preflight()
        
        # Test protected endpoints
        print("\n4. Testing Protected Endpoints...")
        results["protected_endpoints"] = self.test_protected_endpoints()
        
        # Test data operations
        print("\n5. Testing Data Operations...")
        results["data_operations"] = self.test_data_operations()
        
        # Calculate overall success
        endpoint_success = all(results["protected_endpoints"].values())
        data_ops_success = all(results["data_operations"].values()) if results["data_operations"] else True
        
        results["overall_success"] = (
            results["health_check"] and 
            results["login"] and 
            results["cors_preflight"] and 
            endpoint_success
        )
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        status_icon = "✅" if results["overall_success"] else "❌"
        print(f"{status_icon} Overall Status: {'PASS' if results['overall_success'] else 'FAIL'}")
        
        print(f"\n📊 Detailed Results:")
        print(f"   Health Check: {'✅' if results['health_check'] else '❌'}")
        print(f"   Authentication: {'✅' if results['login'] else '❌'}")
        print(f"   CORS Configuration: {'✅' if results['cors_preflight'] else '❌'}")
        
        print(f"\n🔒 Protected Endpoints:")
        for endpoint, success in results["protected_endpoints"].items():
            print(f"   {endpoint}: {'✅' if success else '❌'}")
        
        if results["data_operations"]:
            print(f"\n📝 Data Operations:")
            for operation, success in results["data_operations"].items():
                print(f"   {operation}: {'✅' if success else '❌'}")
        
        return results

def main():
    """Main test execution"""
    tester = APITester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if results["overall_success"] else 1
    print(f"\n🏁 Test completed with exit code: {exit_code}")
    return exit_code

if __name__ == "__main__":
    exit(main())