#!/usr/bin/env python3
"""
System Verification Test Suite
Comprehensive tests to verify all components are working correctly
"""

import os
import sys
import requests
import time
import json
import tempfile
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

class SystemVerificationTests:
    """Comprehensive system verification tests"""
    
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.admin_email = "admin@aishare.com"
        self.admin_password = "admin123"
        self.auth_token = None
        self.test_results = []
    
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
    
    def test_database_connection(self):
        """Test database file exists and is accessible"""
        try:
            db_path = "../storage/aishare_platform.db"
            if os.path.exists(db_path):
                # Try to connect to database
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                conn.close()
                
                if len(tables) > 0:
                    return self.log_test("Database Connection", True, f"Found {len(tables)} tables")
                else:
                    return self.log_test("Database Connection", False, "No tables found")
            else:
                return self.log_test("Database Connection", False, "Database file not found")
        except Exception as e:
            return self.log_test("Database Connection", False, str(e))
    
    def test_backend_health(self):
        """Test backend server health"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                return self.log_test("Backend Health", True, "Server responding")
            else:
                return self.log_test("Backend Health", False, f"Status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            return self.log_test("Backend Health", False, "Connection refused - server not running")
        except Exception as e:
            return self.log_test("Backend Health", False, str(e))
    
    def test_frontend_accessibility(self):
        """Test frontend server accessibility"""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                return self.log_test("Frontend Accessibility", True, "Frontend responding")
            else:
                return self.log_test("Frontend Accessibility", False, f"Status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            return self.log_test("Frontend Accessibility", False, "Connection refused - server not running")
        except Exception as e:
            return self.log_test("Frontend Accessibility", False, str(e))
    
    def test_admin_authentication(self):
        """Test admin user authentication"""
        try:
            login_data = {
                "email": self.admin_email,
                "password": self.admin_password
            }
            response = requests.post(
                f"{self.backend_url}/api/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.auth_token = data["access_token"]
                    return self.log_test("Admin Authentication", True, "Login successful")
                else:
                    return self.log_test("Admin Authentication", False, "No access token in response")
            else:
                return self.log_test("Admin Authentication", False, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Admin Authentication", False, str(e))
    
    def test_api_endpoints(self):
        """Test key API endpoints"""
        if not self.auth_token:
            return self.log_test("API Endpoints", False, "No auth token available")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        endpoints = [
            ("/api/datasets", "Datasets API"),
            ("/api/organizations", "Organizations API"),
            ("/api/users/me", "User Profile API"),
            ("/api/data-connectors/supported-types", "Data Connectors API")
        ]
        
        all_passed = True
        for endpoint, name in endpoints:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", headers=headers, timeout=5)
                if response.status_code in [200, 404]:  # 404 is OK for empty datasets
                    self.log_test(f"API: {name}", True, f"Status: {response.status_code}")
                else:
                    self.log_test(f"API: {name}", False, f"Status: {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log_test(f"API: {name}", False, str(e))
                all_passed = False
        
        return all_passed
    
    def test_document_processing_libraries(self):
        """Test document processing library availability"""
        libraries = [
            ("PyMuPDF", "fitz", "PDF processing"),
            ("python-docx", "docx", "DOCX processing"),
            ("docx2txt", "docx2txt", "DOC processing"),
            ("striprtf", "striprtf.striprtf", "RTF processing"),
            ("odfpy", "odf", "ODT processing")
        ]
        
        all_available = True
        for lib_name, import_name, description in libraries:
            try:
                __import__(import_name)
                self.log_test(f"Library: {lib_name}", True, description)
            except ImportError:
                self.log_test(f"Library: {lib_name}", False, f"Not installed - {description}")
                all_available = False
        
        return all_available
    
    def test_file_upload_simulation(self):
        """Test file upload functionality with a test file"""
        if not self.auth_token:
            return self.log_test("File Upload", False, "No auth token available")
        
        try:
            # Create a test CSV file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                f.write("name,age,city\n")
                f.write("John,25,New York\n")
                f.write("Jane,30,Los Angeles\n")
                f.write("Bob,35,Chicago\n")
                test_file_path = f.name
            
            # Upload the file
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test.csv', f, 'text/csv')}
                data = {'name': 'Test Dataset', 'description': 'Test upload'}
                
                response = requests.post(
                    f"{self.backend_url}/api/datasets/upload",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=30
                )
            
            # Clean up test file
            os.unlink(test_file_path)
            
            if response.status_code in [200, 201]:
                return self.log_test("File Upload", True, "CSV upload successful")
            else:
                return self.log_test("File Upload", False, f"Status: {response.status_code}")
                
        except Exception as e:
            return self.log_test("File Upload", False, str(e))
    
    def test_document_upload_simulation(self):
        """Test document upload functionality"""
        if not self.auth_token:
            return self.log_test("Document Upload", False, "No auth token available")
        
        try:
            # Create a test text document
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("This is a test document for the AI Share Platform.\n")
                f.write("It contains sample text for document processing testing.\n")
                f.write("The platform should extract this text and create a dataset.\n")
                test_file_path = f.name
            
            # Upload the document
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                data = {
                    'dataset_name': 'Test Document',
                    'description': 'Test document upload',
                    'sharing_level': 'PRIVATE'
                }
                
                response = requests.post(
                    f"{self.backend_url}/api/data-connectors/document",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=30
                )
            
            # Clean up test file
            os.unlink(test_file_path)
            
            if response.status_code in [200, 201]:
                return self.log_test("Document Upload", True, "Document upload successful")
            else:
                return self.log_test("Document Upload", False, f"Status: {response.status_code}")
                
        except Exception as e:
            return self.log_test("Document Upload", False, str(e))
    
    def test_environment_configuration(self):
        """Test environment configuration"""
        try:
            # Check main .env file
            env_path = "../.env"
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_content = f.read()
                
                required_vars = [
                    "DATABASE_URL",
                    "SECRET_KEY",
                    "GOOGLE_API_KEY",
                    "MINDSDB_URL"
                ]
                
                missing_vars = []
                for var in required_vars:
                    if var not in env_content:
                        missing_vars.append(var)
                
                if not missing_vars:
                    return self.log_test("Environment Config", True, "All required variables present")
                else:
                    return self.log_test("Environment Config", False, f"Missing: {', '.join(missing_vars)}")
            else:
                return self.log_test("Environment Config", False, ".env file not found")
        except Exception as e:
            return self.log_test("Environment Config", False, str(e))
    
    def test_storage_directories(self):
        """Test storage directory structure"""
        try:
            required_dirs = [
                "../storage",
                "../storage/uploads",
                "../storage/documents",
                "../storage/logs",
                "../storage/backups"
            ]
            
            missing_dirs = []
            for dir_path in required_dirs:
                if not os.path.exists(dir_path):
                    missing_dirs.append(dir_path)
            
            if not missing_dirs:
                return self.log_test("Storage Directories", True, "All directories exist")
            else:
                return self.log_test("Storage Directories", False, f"Missing: {', '.join(missing_dirs)}")
        except Exception as e:
            return self.log_test("Storage Directories", False, str(e))
    
    def run_all_tests(self):
        """Run all verification tests"""
        print("🧪 AI Share Platform - System Verification Tests")
        print("=" * 60)
        
        # Core system tests
        print("\n📋 Core System Tests:")
        self.test_database_connection()
        self.test_environment_configuration()
        self.test_storage_directories()
        
        # Server tests
        print("\n🚀 Server Tests:")
        backend_running = self.test_backend_health()
        frontend_running = self.test_frontend_accessibility()
        
        # Authentication tests
        print("\n🔐 Authentication Tests:")
        auth_working = self.test_admin_authentication()
        
        # API tests (only if backend is running and auth works)
        if backend_running and auth_working:
            print("\n🔌 API Tests:")
            self.test_api_endpoints()
            
            print("\n📁 File Handling Tests:")
            self.test_file_upload_simulation()
            self.test_document_upload_simulation()
        
        # Library tests
        print("\n📚 Library Tests:")
        self.test_document_processing_libraries()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if passed == total:
            print("\n🎉 All tests passed! System is ready for use.")
            return True
        else:
            print("\n⚠️  Some tests failed. Please check the issues above.")
            print("\n🔧 Common fixes:")
            print("   - Ensure servers are running: ./start-dev.sh")
            print("   - Check environment configuration: .env file")
            print("   - Install missing dependencies: pip install -r backend/requirements.txt")
            return False


def main():
    """Main test function"""
    tester = SystemVerificationTests()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())