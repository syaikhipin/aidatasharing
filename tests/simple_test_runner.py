#!/usr/bin/env python3
"""
Simplified Test Runner for AI Share Platform
Tests basic connectivity and API functionality without browser automation
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import Dict, Any

def test_frontend_connectivity() -> Dict[str, Any]:
    """Test frontend server connectivity and basic page access"""
    tests = []
    base_url = "http://localhost:3000"
    
    # Test 1: Frontend server responds
    try:
        response = requests.get(base_url, timeout=10)
        tests.append({
            "name": "Frontend Server Responding",
            "passed": response.status_code == 200,
            "details": f"Status: {response.status_code}"
        })
    except Exception as e:
        tests.append({
            "name": "Frontend Server Responding",
            "passed": False,
            "details": f"Error: {str(e)}"
        })
    
    # Test 2: Authentication pages accessible
    auth_pages = ["/auth/login", "/auth/register"]
    for page in auth_pages:
        try:
            response = requests.get(f"{base_url}{page}", timeout=10)
            tests.append({
                "name": f"Page {page} Accessible",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": f"Page {page} Accessible",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
    
    # Test 3: Protected pages redirect (should get redirected or get 200)
    protected_pages = ["/dashboard", "/datasets", "/models", "/sql", "/analytics"]
    for page in protected_pages:
        try:
            response = requests.get(f"{base_url}{page}", timeout=10, allow_redirects=False)
            # Should either get 200 (page loads with redirect handling) or 3xx (redirect)
            success = response.status_code in [200, 301, 302, 307, 308]
            tests.append({
                "name": f"Protected Page {page} Handles Auth",
                "passed": success,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": f"Protected Page {page} Handles Auth",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
    
    return {
        "total": len(tests),
        "passed": sum(1 for t in tests if t["passed"]),
        "tests": tests
    }

def test_backend_api() -> Dict[str, Any]:
    """Test backend API endpoints and functionality"""
    tests = []
    base_url = "http://localhost:8000"
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        tests.append({
            "name": "Backend Health Check",
            "passed": response.status_code == 200,
            "details": f"Status: {response.status_code}"
        })
    except Exception as e:
        tests.append({
            "name": "Backend Health Check",
            "passed": False,
            "details": f"Error: {str(e)}"
        })
    
    # Test 2: API Documentation
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
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
    
    # Test 3: OpenAPI Schema
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=10)
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
    
    # Test 4: CORS Headers
    try:
        response = requests.options(f"{base_url}/api/auth/login", timeout=10)
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
    
    # Test 5: Authentication endpoint structure
    try:
        # Try to access protected endpoint without auth (should get 401)
        response = requests.get(f"{base_url}/api/auth/me", timeout=10)
        tests.append({
            "name": "Authentication Required",
            "passed": response.status_code == 401,
            "details": f"Status: {response.status_code}"
        })
    except Exception as e:
        tests.append({
            "name": "Authentication Required",
            "passed": False,
            "details": f"Error: {str(e)}"
        })
    
    return {
        "total": len(tests),
        "passed": sum(1 for t in tests if t["passed"]),
        "tests": tests
    }

def test_api_registration_flow() -> Dict[str, Any]:
    """Test user registration flow"""
    tests = []
    base_url = "http://localhost:8000"
    
    # Test registration endpoint exists and handles requests
    try:
        # Create test registration data
        timestamp = int(time.time())
        registration_data = {
            "username": f"testuser_{timestamp}",
            "email": f"testuser_{timestamp}@example.com",
            "password": "testpassword123",
            "organization_option": "create_new",
            "organization_name": f"Test Org {timestamp}",
            "organization_type": "technology"
        }
        
        response = requests.post(f"{base_url}/api/auth/register", json=registration_data, timeout=10)
        
        # Should either succeed (201) or fail with validation error (422)
        success = response.status_code in [201, 422]
        tests.append({
            "name": "Registration Endpoint Functional",
            "passed": success,
            "details": f"Status: {response.status_code}"
        })
        
        # If successful, test login
        if response.status_code == 201:
            try:
                login_data = {
                    "email": registration_data["email"],
                    "password": registration_data["password"]
                }
                login_response = requests.post(f"{base_url}/api/auth/login", json=login_data, timeout=10)
                
                tests.append({
                    "name": "Login After Registration",
                    "passed": login_response.status_code == 200,
                    "details": f"Status: {login_response.status_code}"
                })
                
            except Exception as e:
                tests.append({
                    "name": "Login After Registration",
                    "passed": False,
                    "details": f"Error: {str(e)}"
                })
        
    except Exception as e:
        tests.append({
            "name": "Registration Endpoint Functional",
            "passed": False,
            "details": f"Error: {str(e)}"
        })
    
    return {
        "total": len(tests),
        "passed": sum(1 for t in tests if t["passed"]),
        "tests": tests
    }

def test_database_connectivity() -> Dict[str, Any]:
    """Test database connectivity through API endpoints"""
    tests = []
    base_url = "http://localhost:8000"
    
    # Test endpoints that require database access
    db_endpoints = [
        ("/organizations/", "Organizations List"),
        ("/datasets/", "Datasets List"),
        ("/models/", "Models List")
    ]
    
    for endpoint, name in db_endpoints:
        try:
            # Should get 401 (unauthorized) which means the endpoint works but requires auth
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            tests.append({
                "name": f"{name} Endpoint Responds",
                "passed": response.status_code in [200, 401],
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            tests.append({
                "name": f"{name} Endpoint Responds",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
    
    return {
        "total": len(tests),
        "passed": sum(1 for t in tests if t["passed"]),
        "tests": tests
    }

def generate_test_report(results: Dict[str, Any]) -> str:
    """Generate a comprehensive test report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Calculate totals
    total_tests = sum(result.get("total", 0) for result in results.values())
    total_passed = sum(result.get("passed", 0) for result in results.values())
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    report = f"""
# AI Share Platform - Test Report
Generated: {timestamp}

## Summary
- **Total Tests**: {total_tests}
- **Passed**: {total_passed}
- **Failed**: {total_tests - total_passed}
- **Success Rate**: {success_rate:.1f}%

"""
    
    # Overall status
    if success_rate >= 95:
        status = "🟢 EXCELLENT"
    elif success_rate >= 85:
        status = "🟡 GOOD"
    elif success_rate >= 70:
        status = "🟠 NEEDS IMPROVEMENT"
    else:
        status = "🔴 CRITICAL ISSUES"
    
    report += f"**Status**: {status}\n\n"
    
    # Detailed results
    for test_category, test_results in results.items():
        report += f"## {test_category.replace('_', ' ').title()}\n"
        report += f"**Tests**: {test_results['passed']}/{test_results['total']} passed\n\n"
        
        for test in test_results["tests"]:
            status_icon = "✅" if test["passed"] else "❌"
            report += f"- {status_icon} **{test['name']}**: {test['details']}\n"
        report += "\n"
    
    # Recommendations
    report += "## Recommendations\n\n"
    if success_rate >= 95:
        report += "🎉 Excellent! Platform is working well.\n"
    elif success_rate >= 85:
        report += "👍 Good progress! Minor issues to address.\n"
    elif success_rate >= 70:
        report += "⚠️ Several issues need attention.\n"
    else:
        report += "🚨 Critical issues detected. Check server configuration.\n"
    
    return report

def main():
    """Main test runner"""
    print("🚀 AI Share Platform - Simplified Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all test categories
    results = {}
    
    print("\n🖥️  Testing Frontend Connectivity...")
    results["frontend_connectivity"] = test_frontend_connectivity()
    print(f"✅ Frontend: {results['frontend_connectivity']['passed']}/{results['frontend_connectivity']['total']} passed")
    
    print("\n🔧 Testing Backend API...")
    results["backend_api"] = test_backend_api()
    print(f"✅ Backend: {results['backend_api']['passed']}/{results['backend_api']['total']} passed")
    
    print("\n👤 Testing Registration Flow...")
    results["registration_flow"] = test_api_registration_flow()
    print(f"✅ Registration: {results['registration_flow']['passed']}/{results['registration_flow']['total']} passed")
    
    print("\n💾 Testing Database Connectivity...")
    results["database_connectivity"] = test_database_connectivity()
    print(f"✅ Database: {results['database_connectivity']['passed']}/{results['database_connectivity']['total']} passed")
    
    # Generate report
    report = generate_test_report(results)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("test_results", exist_ok=True)
    
    # Save JSON results
    json_file = f"test_results/simple_test_results_{timestamp}.json"
    with open(json_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Save report
    report_file = f"test_results/simple_test_report_{timestamp}.md"
    with open(report_file, "w") as f:
        f.write(report)
    
    # Print summary
    total_tests = sum(result.get("total", 0) for result in results.values())
    total_passed = sum(result.get("passed", 0) for result in results.values())
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print("\n" + "=" * 60)
    print("🎯 Test Results Summary:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {total_passed}")
    print(f"   Failed: {total_tests - total_passed}")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"\n📊 Results saved to: {json_file}")
    print(f"📝 Report saved to: {report_file}")
    
    return success_rate >= 80.0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 