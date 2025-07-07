#!/usr/bin/env python3
"""
Unified Test Runner for AI Share Platform
Runs comprehensive backend and frontend tests with detailed reporting
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, Any, List
import requests

def check_server_status(url: str, name: str, timeout: int = 5) -> bool:
    """Check if a server is running and responding"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code in [200, 404]  # 404 is OK for Next.js routing
    except requests.exceptions.RequestException:
        return False

def install_dependencies() -> bool:
    """Install required test dependencies"""
    dependencies = [
        "requests",
        "selenium",
        "pytest",
        "webdriver-manager"
    ]
    
    print("📦 Installing test dependencies...")
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=True, capture_output=True)
            print(f"✅ Installed {dep}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {dep}")
            return False
    
    return True

def run_backend_tests() -> Dict[str, Any]:
    """Run backend test suite"""
    print("\n🔧 Running Backend Tests")
    print("=" * 50)
    
    # Check if backend is running
    if not check_server_status("http://localhost:8000/health", "Backend"):
        print("❌ Backend server not running. Starting backend...")
        try:
            # Try to start backend
            backend_process = subprocess.Popen(
                [sys.executable, "start.py"],
                cwd="backend",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(5)  # Give it time to start
            
            if not check_server_status("http://localhost:8000/health", "Backend"):
                print("❌ Failed to start backend server")
                return {"error": "Backend server not available"}
        except Exception as e:
            print(f"❌ Error starting backend: {e}")
            return {"error": f"Backend startup failed: {e}"}
    
    # Import and run backend tests
    try:
        sys.path.append('tests')
        from test_backend import BackendTestSuite
        
        test_suite = BackendTestSuite()
        results = test_suite.run_all_tests()
        return results
    except Exception as e:
        print(f"❌ Backend tests failed: {e}")
        return {"error": f"Backend test execution failed: {e}"}

def run_frontend_tests() -> Dict[str, Any]:
    """Run frontend test suite"""
    print("\n🖥️  Running Frontend Tests")
    print("=" * 50)
    
    # Check if frontend is running
    if not check_server_status("http://localhost:3000", "Frontend"):
        print("❌ Frontend server not running. Please start with: cd frontend && npm run dev")
        return {"error": "Frontend server not available"}
    
    # Check if ChromeDriver is available
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=options)
        driver.quit()
    except Exception as e:
        print(f"❌ ChromeDriver not available: {e}")
        print("Please install ChromeDriver or run tests manually")
        return {"error": f"ChromeDriver not available: {e}"}
    
    # Import and run frontend tests
    try:
        from test_frontend import FrontendTestSuite
        
        test_suite = FrontendTestSuite()
        results = test_suite.run_all_tests()
        return results
    except Exception as e:
        print(f"❌ Frontend tests failed: {e}")
        return {"error": f"Frontend test execution failed: {e}"}

def run_gemini_sdk_tests() -> Dict[str, Any]:
    """Run Gemini SDK integration tests"""
    print("\n🧠 Running Gemini SDK Integration Tests")
    print("=" * 50)
    
    try:
        # Import and run Gemini SDK tests
        sys.path.append('tests')
        from test_gemini_sdk_integration import GeminiSDKIntegrationTest
        
        test_suite = GeminiSDKIntegrationTest()
        success = test_suite.run_all_tests()
        
        # Return results in consistent format
        results = test_suite.test_results
        return {
            "total": results["total_tests"],
            "passed": results["passed"],
            "failed": results["failed"],
            "success": success,
            "details": results["test_details"],
            "errors": results["errors"]
        }
        
    except Exception as e:
        print(f"❌ Gemini SDK tests failed: {e}")
        return {
            "total": 1,
            "passed": 0,
            "failed": 1,
            "success": False,
            "errors": [f"Gemini SDK test execution failed: {e}"]
        }

def run_integration_tests() -> Dict[str, Any]:
    """Run integration tests that test full workflows"""
    print("\n🔄 Running Integration Tests")
    print("=" * 50)
    
    # Simple integration test - check if both servers respond
    tests = []
    
    # Test 1: Backend health
    backend_ok = check_server_status("http://localhost:8000/health", "Backend")
    tests.append({
        "name": "Backend Server Health",
        "passed": backend_ok,
        "details": f"Backend responding: {backend_ok}"
    })
    
    # Test 2: Frontend health
    frontend_ok = check_server_status("http://localhost:3000", "Frontend")
    tests.append({
        "name": "Frontend Server Health",
        "passed": frontend_ok,
        "details": f"Frontend responding: {frontend_ok}"
    })
    
    # Test 3: API documentation accessible
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        api_docs_ok = response.status_code == 200
        tests.append({
            "name": "API Documentation Accessible",
            "passed": api_docs_ok,
            "details": f"API docs status: {response.status_code}"
        })
    except Exception as e:
        tests.append({
            "name": "API Documentation Accessible",
            "passed": False,
            "details": f"Error: {str(e)}"
        })
    
    return {
        "total": len(tests),
        "passed": sum(1 for t in tests if t["passed"]),
        "tests": tests
    }

def generate_comprehensive_report(results: Dict[str, Any]) -> str:
    """Generate a comprehensive test report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
# AI Share Platform - Comprehensive Test Report
Generated: {timestamp}

## Executive Summary

"""
    
    total_tests = 0
    total_passed = 0
    
    for test_type, test_results in results.items():
        if isinstance(test_results, dict) and "summary" in test_results:
            summary = test_results["summary"]
            total_tests += summary.get("total_tests", 0)
            total_passed += summary.get("passed_tests", 0)
    
    if total_tests > 0:
        success_rate = (total_passed / total_tests) * 100
        report += f"- **Total Tests**: {total_tests}\n"
        report += f"- **Passed**: {total_passed}\n"
        report += f"- **Failed**: {total_tests - total_passed}\n"
        report += f"- **Success Rate**: {success_rate:.1f}%\n"
    else:
        success_rate = 0
        report += f"- **Total Tests**: 0\n"
        report += f"- **Status**: No tests executed\n"
    
    # Overall status
    if success_rate >= 95:
        status = "🟢 EXCELLENT"
    elif success_rate >= 85:
        status = "🟡 GOOD"
    elif success_rate >= 70:
        status = "🟠 NEEDS IMPROVEMENT"
    else:
        status = "🔴 CRITICAL ISSUES"
    
    report += f"- **Overall Status**: {status}\n\n"
    
    # Detailed results by test type
    for test_type, test_results in results.items():
        report += f"## {test_type.title()} Test Results\n\n"
        
        if isinstance(test_results, dict) and "error" in test_results:
            report += f"❌ **Error**: {test_results['error']}\n\n"
            continue
        
        if "summary" in test_results:
            summary = test_results["summary"]
            report += f"- Tests Run: {summary.get('total_tests', 0)}\n"
            report += f"- Passed: {summary.get('passed_tests', 0)}\n"
            report += f"- Failed: {summary.get('failed_tests', 0)}\n"
            report += f"- Success Rate: {summary.get('success_rate', 0):.1f}%\n\n"
        
        # Test details
        if "tests" in test_results:
            if isinstance(test_results["tests"], dict):
                for category, category_results in test_results["tests"].items():
                    report += f"### {category}\n"
                    if isinstance(category_results, dict) and "tests" in category_results:
                        for test in category_results["tests"]:
                            status_icon = "✅" if test["passed"] else "❌"
                            report += f"- {status_icon} {test['name']}: {test['details']}\n"
                    report += "\n"
            elif isinstance(test_results["tests"], list):
                for test in test_results["tests"]:
                    status_icon = "✅" if test["passed"] else "❌"
                    report += f"- {status_icon} {test['name']}: {test['details']}\n"
                report += "\n"
    
    # Recommendations
    report += "## Recommendations\n\n"
    
    if success_rate >= 95:
        report += "🎉 Excellent! Your platform is ready for production.\n"
    elif success_rate >= 85:
        report += "👍 Good progress! Address the failing tests before production.\n"
    elif success_rate >= 70:
        report += "⚠️ Several issues need attention before production deployment.\n"
    else:
        report += "🚨 Critical issues detected. Significant work needed before production.\n"
    
    return report

def main():
    """Main test runner function"""
    print("🚀 AI Share Platform - Comprehensive Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Install dependencies
    print("\n📋 Checking Dependencies...")
    if not install_dependencies():
        print("❌ Failed to install required dependencies")
        return False
    
    # Create results directory
    os.makedirs("test_results", exist_ok=True)
    
    # Run all test suites
    all_results = {}
    
    # Backend tests
    backend_results = run_backend_tests()
    all_results["backend"] = backend_results
    
    # Frontend tests (if ChromeDriver is available)
    try:
        frontend_results = run_frontend_tests()
        all_results["frontend"] = frontend_results
    except Exception as e:
        print(f"⚠️ Frontend tests skipped: {e}")
        all_results["frontend"] = {"error": f"Skipped: {e}"}
    
    # Gemini SDK tests
    try:
        gemini_results = run_gemini_sdk_tests()
        all_results["gemini_sdk"] = gemini_results
    except Exception as e:
        print(f"⚠️ Gemini SDK tests skipped: {e}")
        all_results["gemini_sdk"] = {"error": f"Skipped: {e}"}
    
    # Integration tests
    integration_results = run_integration_tests()
    all_results["integration"] = integration_results
    
    # Generate comprehensive report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON results
    json_file = f"test_results/comprehensive_test_results_{timestamp}.json"
    with open(json_file, "w") as f:
        json.dump(all_results, f, indent=2)
    
    # Generate and save markdown report
    report = generate_comprehensive_report(all_results)
    report_file = f"test_results/test_report_{timestamp}.md"
    with open(report_file, "w") as f:
        f.write(report)
    
    # Print summary
    print("\n" + "=" * 60)
    print("🎯 Test Execution Complete!")
    print(f"📊 Results saved to: {json_file}")
    print(f"📝 Report saved to: {report_file}")
    
    # Calculate overall success
    total_tests = 0
    total_passed = 0
    
    for test_results in all_results.values():
        if isinstance(test_results, dict):
            if "summary" in test_results:
                summary = test_results["summary"]
                total_tests += summary.get("total_tests", 0)
                total_passed += summary.get("passed_tests", 0)
            elif "total" in test_results:
                total_tests += test_results.get("total", 0)
                total_passed += test_results.get("passed", 0)
    
    if total_tests > 0:
        success_rate = (total_passed / total_tests) * 100
        print(f"🎯 Overall Success Rate: {success_rate:.1f}% ({total_passed}/{total_tests})")
        
        return success_rate >= 80.0
    
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 