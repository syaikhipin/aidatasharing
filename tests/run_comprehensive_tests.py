#!/usr/bin/env python3
"""
Comprehensive Test Runner for AI Share Platform
Runs both offline and online tests to verify the complete system
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

class ComprehensiveTestRunner:
    """Comprehensive test runner for the AI Share Platform"""
    
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_results = []
        self.servers_started = False
    
    def log_test(self, test_name, success, message=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        return success
    
    def run_offline_tests(self):
        """Run offline verification tests"""
        print("🔧 Running Offline Tests...")
        print("-" * 40)
        
        try:
            result = subprocess.run([
                sys.executable, "test_offline_verification.py"
            ], capture_output=True, text=True, cwd=".")
            
            if result.returncode == 0:
                return self.log_test("Offline Tests", True, "All offline tests passed")
            else:
                return self.log_test("Offline Tests", False, "Some offline tests failed")
        except Exception as e:
            return self.log_test("Offline Tests", False, str(e))
    
    def check_servers_running(self):
        """Check if servers are already running"""
        try:
            # Check backend
            backend_response = requests.get(f"{self.backend_url}/health", timeout=2)
            backend_running = backend_response.status_code == 200
        except:
            backend_running = False
        
        try:
            # Check frontend
            frontend_response = requests.get(self.frontend_url, timeout=2)
            frontend_running = frontend_response.status_code == 200
        except:
            frontend_running = False
        
        return backend_running, frontend_running
    
    def start_servers(self):
        """Start development servers"""
        print("🚀 Starting Development Servers...")
        print("-" * 40)
        
        # Check if servers are already running
        backend_running, frontend_running = self.check_servers_running()
        
        if backend_running and frontend_running:
            self.log_test("Server Status", True, "Servers already running")
            self.servers_started = True
            return True
        
        # Start servers using the development script
        try:
            # Change to project root directory
            project_root = Path(__file__).parent.parent
            
            # Start development environment
            print("   Starting servers with ./start-dev.sh...")
            process = subprocess.Popen(
                ["./start-dev.sh"],
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for servers to start
            print("   Waiting for servers to start...")
            max_wait = 60  # Maximum wait time in seconds
            wait_time = 0
            
            while wait_time < max_wait:
                time.sleep(2)
                wait_time += 2
                
                backend_running, frontend_running = self.check_servers_running()
                
                if backend_running and frontend_running:
                    self.log_test("Server Startup", True, f"Servers started in {wait_time}s")
                    self.servers_started = True
                    return True
                elif wait_time % 10 == 0:
                    print(f"   Still waiting... ({wait_time}s)")
            
            self.log_test("Server Startup", False, f"Servers failed to start within {max_wait}s")
            return False
            
        except Exception as e:
            self.log_test("Server Startup", False, str(e))
            return False
    
    def run_online_tests(self):
        """Run online tests that require servers"""
        if not self.servers_started:
            return self.log_test("Online Tests", False, "Servers not running")
        
        print("\n🌐 Running Online Tests...")
        print("-" * 40)
        
        try:
            result = subprocess.run([
                sys.executable, "test_system_verification.py"
            ], capture_output=True, text=True, cwd=".")
            
            if result.returncode == 0:
                return self.log_test("Online Tests", True, "All online tests passed")
            else:
                # Print the output for debugging
                print("Online test output:")
                print(result.stdout)
                if result.stderr:
                    print("Errors:")
                    print(result.stderr)
                return self.log_test("Online Tests", False, "Some online tests failed")
        except Exception as e:
            return self.log_test("Online Tests", False, str(e))
    
    def run_specific_tests(self):
        """Run specific feature tests"""
        print("\n🧪 Running Specific Feature Tests...")
        print("-" * 40)
        
        # Test document processing
        try:
            result = subprocess.run([
                sys.executable, "test_simple_document.py"
            ], capture_output=True, text=True, cwd=".")
            
            if result.returncode == 0:
                self.log_test("Document Processing", True, "Document processing tests passed")
            else:
                self.log_test("Document Processing", False, "Document processing tests failed")
        except Exception as e:
            self.log_test("Document Processing", False, str(e))
    
    def stop_servers(self):
        """Stop development servers"""
        if self.servers_started:
            print("\n🛑 Stopping Development Servers...")
            print("-" * 40)
            
            try:
                project_root = Path(__file__).parent.parent
                subprocess.run(["./stop-dev.sh"], cwd=project_root, timeout=10)
                self.log_test("Server Shutdown", True, "Servers stopped successfully")
            except Exception as e:
                self.log_test("Server Shutdown", False, str(e))
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🧪 AI Share Platform - Comprehensive Test Suite")
        print("=" * 60)
        print("This will run offline tests, start servers, and run online tests")
        print()
        
        # Step 1: Run offline tests
        offline_success = self.run_offline_tests()
        
        if not offline_success:
            print("\n❌ Offline tests failed. Please fix issues before running online tests.")
            return False
        
        # Step 2: Start servers and run online tests
        if self.start_servers():
            # Give servers a moment to fully initialize
            time.sleep(5)
            
            # Run online tests
            online_success = self.run_online_tests()
            
            # Run specific feature tests
            self.run_specific_tests()
            
            # Stop servers
            self.stop_servers()
        else:
            online_success = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Comprehensive Test Summary:")
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if passed == total:
            print("\n🎉 All tests passed! System is fully functional.")
            print("\n🚀 Ready for manual testing:")
            print("   1. Start servers: ./start-dev.sh")
            print("   2. Open frontend: http://localhost:3000")
            print("   3. Login with: admin@aishare.com / admin123")
            return True
        else:
            print("\n⚠️  Some tests failed. Please check the issues above.")
            print("\n🔧 Common fixes:")
            print("   - Check server logs for errors")
            print("   - Verify environment configuration")
            print("   - Ensure all dependencies are installed")
            return False


def main():
    """Main test function"""
    runner = ComprehensiveTestRunner()
    success = runner.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())