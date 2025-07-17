#!/usr/bin/env python3
"""
Offline System Verification Test Suite
Tests that can be run without starting the servers
"""

import os
import sys
import sqlite3
import tempfile
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

class OfflineVerificationTests:
    """Offline system verification tests"""
    
    def __init__(self):
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
    
    def test_project_structure(self):
        """Test project directory structure"""
        try:
            required_dirs = [
                "../backend",
                "../frontend", 
                "../storage",
                "../tests",
                "../docs",
                "../migrations"
            ]
            
            missing_dirs = []
            for dir_path in required_dirs:
                if not os.path.exists(dir_path):
                    missing_dirs.append(dir_path)
            
            if not missing_dirs:
                return self.log_test("Project Structure", True, "All directories exist")
            else:
                return self.log_test("Project Structure", False, f"Missing: {', '.join(missing_dirs)}")
        except Exception as e:
            return self.log_test("Project Structure", False, str(e))
    
    def test_database_file(self):
        """Test database file exists and has correct schema"""
        try:
            db_path = "../storage/aishare_platform.db"
            if not os.path.exists(db_path):
                return self.log_test("Database File", False, "Database file not found")
            
            # Connect to database and check tables
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Check for required tables
            required_tables = ['users', 'organizations', 'datasets', 'database_connectors']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if not missing_tables:
                # Check for document processing columns in datasets table
                cursor.execute("PRAGMA table_info(datasets);")
                columns = [row[1] for row in cursor.fetchall()]
                
                document_columns = ['document_type', 'page_count', 'word_count', 'extracted_text']
                missing_columns = [col for col in document_columns if col not in columns]
                
                conn.close()
                
                if not missing_columns:
                    return self.log_test("Database Schema", True, f"Found {len(tables)} tables with document support")
                else:
                    return self.log_test("Database Schema", False, f"Missing columns: {', '.join(missing_columns)}")
            else:
                conn.close()
                return self.log_test("Database Schema", False, f"Missing tables: {', '.join(missing_tables)}")
                
        except Exception as e:
            return self.log_test("Database File", False, str(e))
    
    def test_environment_files(self):
        """Test environment configuration files"""
        try:
            env_files = [
                ("../.env", "Main environment file"),
                ("../.env.example", "Environment template"),
                ("../backend/.env", "Backend environment"),
                ("../frontend/.env.local", "Frontend environment")
            ]
            
            all_exist = True
            for file_path, description in env_files:
                if os.path.exists(file_path):
                    self.log_test(f"Env File: {description}", True, "File exists")
                else:
                    self.log_test(f"Env File: {description}", False, "File missing")
                    all_exist = False
            
            return all_exist
        except Exception as e:
            return self.log_test("Environment Files", False, str(e))
    
    def test_backend_dependencies(self):
        """Test backend Python dependencies"""
        try:
            # Test core dependencies
            dependencies = [
                ("fastapi", "FastAPI web framework"),
                ("sqlalchemy", "Database ORM"),
                ("pydantic", "Data validation"),
                ("uvicorn", "ASGI server"),
                ("jose", "JWT handling"),
                ("passlib", "Password hashing"),
                ("pandas", "Data processing"),
                ("requests", "HTTP client")
            ]
            
            all_available = True
            for dep_name, description in dependencies:
                try:
                    __import__(dep_name)
                    self.log_test(f"Dependency: {dep_name}", True, description)
                except ImportError:
                    self.log_test(f"Dependency: {dep_name}", False, f"Not installed - {description}")
                    all_available = False
            
            return all_available
        except Exception as e:
            return self.log_test("Backend Dependencies", False, str(e))
    
    def test_document_processing_libraries(self):
        """Test document processing libraries"""
        try:
            libraries = [
                ("fitz", "PyMuPDF", "PDF processing"),
                ("docx", "python-docx", "DOCX processing"),
                ("docx2txt", "docx2txt", "DOC processing")
            ]
            
            available_count = 0
            for import_name, lib_name, description in libraries:
                try:
                    __import__(import_name)
                    self.log_test(f"Doc Library: {lib_name}", True, description)
                    available_count += 1
                except ImportError:
                    self.log_test(f"Doc Library: {lib_name}", False, f"Not installed - {description}")
            
            return available_count > 0  # At least one library should be available
        except Exception as e:
            return self.log_test("Document Libraries", False, str(e))
    
    def test_backend_models(self):
        """Test backend model imports"""
        try:
            # Test model imports
            from app.models.user import User
            from app.models.organization import Organization
            from app.models.dataset import Dataset, DatasetType, DatasetStatus
            
            self.log_test("Backend Models", True, "All models import successfully")
            
            # Test enum values
            dataset_types = [dt.value for dt in DatasetType]
            if 'pdf' in dataset_types and 'docx' in dataset_types:
                self.log_test("Document Types", True, "Document types available in enum")
            else:
                self.log_test("Document Types", False, f"Document types missing from enum. Available: {dataset_types}")
            
            return True
        except Exception as e:
            return self.log_test("Backend Models", False, str(e))
    
    def test_backend_services(self):
        """Test backend service imports"""
        try:
            from app.services.connector_service import ConnectorService
            from app.core.database import get_db
            from app.core.config import settings
            
            self.log_test("Backend Services", True, "Core services import successfully")
            
            # Test configuration
            if hasattr(settings, 'DATABASE_URL') and 'aishare_platform.db' in settings.DATABASE_URL:
                self.log_test("Database Config", True, "Database URL points to unified database")
            else:
                self.log_test("Database Config", False, "Database URL not configured correctly")
            
            return True
        except Exception as e:
            return self.log_test("Backend Services", False, str(e))
    
    def test_frontend_structure(self):
        """Test frontend file structure"""
        try:
            frontend_files = [
                ("../frontend/package.json", "Package configuration"),
                ("../frontend/next.config.ts", "Next.js configuration"),
                ("../frontend/tailwind.config.js", "Tailwind CSS configuration"),
                ("../frontend/src/app/page.tsx", "Main page component"),
                ("../frontend/src/app/datasets/page.tsx", "Datasets page"),
                ("../frontend/src/components/DocumentUploader.tsx", "Document uploader component")
            ]
            
            all_exist = True
            for file_path, description in frontend_files:
                if os.path.exists(file_path):
                    self.log_test(f"Frontend: {description}", True, "File exists")
                else:
                    self.log_test(f"Frontend: {description}", False, "File missing")
                    all_exist = False
            
            return all_exist
        except Exception as e:
            return self.log_test("Frontend Structure", False, str(e))
    
    def test_documentation(self):
        """Test documentation files"""
        try:
            doc_files = [
                ("../README.md", "Main README"),
                ("../docs/PROJECT_STRUCTURE.md", "Project structure"),
                ("../docs/TESTING_GUIDE.md", "Testing guide"),
                ("../docs/ENHANCED_DATASET_MANAGEMENT.md", "Feature documentation"),
                ("../docs/MIGRATION_SUMMARY.md", "Migration summary")
            ]
            
            all_exist = True
            for file_path, description in doc_files:
                if os.path.exists(file_path):
                    self.log_test(f"Documentation: {description}", True, "File exists")
                else:
                    self.log_test(f"Documentation: {description}", False, "File missing")
                    all_exist = False
            
            return all_exist
        except Exception as e:
            return self.log_test("Documentation", False, str(e))
    
    def test_startup_scripts(self):
        """Test startup and utility scripts"""
        try:
            scripts = [
                ("../setup_fresh_install.py", "Fresh installation script"),
                ("../start-dev.sh", "Development startup script"),
                ("../stop-dev.sh", "Development stop script"),
                ("../migrations/fresh_install_migration.py", "Database migration script")
            ]
            
            all_exist = True
            for file_path, description in scripts:
                if os.path.exists(file_path):
                    # Check if script is executable (for .sh files)
                    if file_path.endswith('.sh'):
                        if os.access(file_path, os.X_OK):
                            self.log_test(f"Script: {description}", True, "File exists and executable")
                        else:
                            self.log_test(f"Script: {description}", False, "File exists but not executable")
                            all_exist = False
                    else:
                        self.log_test(f"Script: {description}", True, "File exists")
                else:
                    self.log_test(f"Script: {description}", False, "File missing")
                    all_exist = False
            
            return all_exist
        except Exception as e:
            return self.log_test("Startup Scripts", False, str(e))
    
    def test_simple_document_processing(self):
        """Test document processing without database"""
        try:
            # Create a simple text file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("This is a test document.\nIt has multiple lines.\nFor testing purposes.")
                test_file_path = f.name
            
            # Test text processing
            with open(test_file_path, 'r') as f:
                content = f.read()
            
            word_count = len(content.split())
            line_count = len(content.splitlines())
            
            # Clean up
            os.unlink(test_file_path)
            
            if word_count > 0 and line_count > 0:
                return self.log_test("Document Processing", True, f"Processed {word_count} words, {line_count} lines")
            else:
                return self.log_test("Document Processing", False, "Failed to process text")
                
        except Exception as e:
            return self.log_test("Document Processing", False, str(e))
    
    def run_all_tests(self):
        """Run all offline verification tests"""
        print("🧪 AI Share Platform - Offline Verification Tests")
        print("=" * 60)
        print("ℹ️  These tests verify the system without starting servers")
        
        # Project structure tests
        print("\n📁 Project Structure Tests:")
        self.test_project_structure()
        self.test_startup_scripts()
        
        # Configuration tests
        print("\n⚙️  Configuration Tests:")
        self.test_environment_files()
        
        # Database tests
        print("\n🗄️  Database Tests:")
        self.test_database_file()
        
        # Backend tests
        print("\n🔧 Backend Tests:")
        self.test_backend_dependencies()
        self.test_backend_models()
        self.test_backend_services()
        
        # Frontend tests
        print("\n🎨 Frontend Tests:")
        self.test_frontend_structure()
        
        # Document processing tests
        print("\n📄 Document Processing Tests:")
        self.test_document_processing_libraries()
        self.test_simple_document_processing()
        
        # Documentation tests
        print("\n📚 Documentation Tests:")
        self.test_documentation()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if passed == total:
            print("\n🎉 All offline tests passed! System structure is correct.")
            print("🚀 Ready to start servers with: ./start-dev.sh")
            return True
        else:
            print("\n⚠️  Some tests failed. Please check the issues above.")
            print("\n🔧 Common fixes:")
            print("   - Run fresh installation: python setup_fresh_install.py")
            print("   - Install dependencies: pip install -r backend/requirements.txt")
            print("   - Check file permissions: chmod +x *.sh")
            return False


def main():
    """Main test function"""
    tester = OfflineVerificationTests()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())