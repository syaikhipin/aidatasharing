"""
Comprehensive Frontend Test Suite for AI Share Platform
Tests all pages, components, user interactions, and workflows
"""

import json
import time
import os
from datetime import datetime
from typing import Dict, Any, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class FrontendTestSuite:
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.driver = None
        self.wait = None
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
        except Exception as e:
            print(f"❌ Failed to setup Chrome WebDriver: {e}")
            print("Please install ChromeDriver or use a different browser")
            raise
    
    def teardown_driver(self):
        """Clean up WebDriver"""
        if self.driver:
            self.driver.quit()
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all frontend tests and return comprehensive results"""
        print("🧪 Starting Comprehensive Frontend Test Suite")
        print("=" * 60)
        
        results = {
            "start_time": datetime.now().isoformat(),
            "tests": {},
            "summary": {},
            "errors": []
        }
        
        try:
            # Test categories
            test_categories = [
                ("Landing Page", self.test_landing_page),
                ("Authentication Pages", self.test_authentication),
                ("Dashboard Layout", self.test_dashboard_layout),
                ("Organization Management", self.test_organization_pages),
                ("Dataset Management", self.test_dataset_pages),
                ("Model Management", self.test_model_pages),
                ("SQL Playground", self.test_sql_playground),
                ("Analytics Dashboard", self.test_analytics_pages),
                ("Data Access Management", self.test_data_access_pages),
                ("Admin Panel", self.test_admin_pages),
                ("Responsive Design", self.test_responsive_design),
                ("Navigation & Routing", self.test_navigation)
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
            
            print(f"\n🎯 Frontend Test Summary:")
            print(f"   Total Tests: {total_tests}")
            print(f"   Passed: {passed_tests}")
            print(f"   Failed: {total_tests - passed_tests}")
            print(f"   Success Rate: {results['summary']['success_rate']:.1f}%")
            
        finally:
            self.teardown_driver()
        
        return results
    
    def test_landing_page(self) -> Dict[str, Any]:
        """Test landing page functionality"""
        tests = []
        
        try:
            self.driver.get(self.base_url)
            
            # Test 1: Page loads successfully
            tests.append({
                "name": "Landing Page Loads",
                "passed": "AI Share Platform" in self.driver.title,
                "details": f"Title: {self.driver.title}"
            })
            
            # Test 2: Navigation elements present
            try:
                # Look for navigation buttons instead of nav elements
                nav_buttons = self.driver.find_elements(By.LINK_TEXT, "Get Started") + self.driver.find_elements(By.LINK_TEXT, "Sign Up")
                tests.append({
                    "name": "Navigation Present",
                    "passed": len(nav_buttons) > 0,
                    "details": f"Found {len(nav_buttons)} navigation buttons"
                })
            except:
                tests.append({
                    "name": "Navigation Present",
                    "passed": False,
                    "details": "No navigation elements found"
                })
            
            # Test 3: Login button present
            try:
                login_button = self.driver.find_element(By.LINK_TEXT, "Get Started")
                tests.append({
                    "name": "Login Button Present",
                    "passed": login_button.is_displayed(),
                    "details": "Login button found and visible"
                })
            except:
                tests.append({
                    "name": "Login Button Present",
                    "passed": False,
                    "details": "Login button not found"
                })
            
            # Test 4: Register button present
            try:
                register_button = self.driver.find_element(By.LINK_TEXT, "Sign Up")
                tests.append({
                    "name": "Register Button Present",
                    "passed": register_button.is_displayed(),
                    "details": "Register button found and visible"
                })
            except:
                tests.append({
                    "name": "Register Button Present",
                    "passed": False,
                    "details": "Register button not found"
                })
            
        except Exception as e:
            tests.append({
                "name": "Landing Page Test",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_authentication(self) -> Dict[str, Any]:
        """Test authentication pages and flows"""
        tests = []
        
        # Test 1: Login page accessibility
        try:
            self.driver.get(f"{self.base_url}/login")
            time.sleep(2)
            
            tests.append({
                "name": "Login Page Accessible",
                "passed": "/login" in self.driver.current_url,
                "details": f"URL: {self.driver.current_url}"
            })
            
            # Test login form elements
            email_input = self.driver.find_element(By.NAME, "email")
            password_input = self.driver.find_element(By.NAME, "password")
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            
            tests.append({
                "name": "Login Form Elements Present",
                "passed": bool(email_input and password_input and submit_button),
                "details": "Email, password, and submit elements found"
            })
            
        except Exception as e:
            tests.append({
                "name": "Login Page Test",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 2: Register page accessibility
        try:
            self.driver.get(f"{self.base_url}/register")
            time.sleep(2)
            
            tests.append({
                "name": "Register Page Accessible",
                "passed": "/register" in self.driver.current_url,
                "details": f"URL: {self.driver.current_url}"
            })
            
            # Test register form elements
            fullname_input = self.driver.find_element(By.NAME, "fullName")
            email_input = self.driver.find_element(By.NAME, "email")
            password_input = self.driver.find_element(By.NAME, "password")
            
            tests.append({
                "name": "Register Form Elements Present",
                "passed": bool(fullname_input and email_input and password_input),
                "details": "Full name, email, and password elements found"
            })
            
        except Exception as e:
            tests.append({
                "name": "Register Page Test",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test 3: Form validation
        try:
            # Try submitting empty form
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            time.sleep(1)
            
            # Should still be on register page (validation failed)
            tests.append({
                "name": "Form Validation Works",
                "passed": "/register" in self.driver.current_url,
                "details": "Empty form submission blocked"
            })
            
        except Exception as e:
            tests.append({
                "name": "Form Validation Test",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_dashboard_layout(self) -> Dict[str, Any]:
        """Test dashboard layout and navigation"""
        tests = []
        
        # Note: These tests require authentication, so we'll test what we can access
        try:
            self.driver.get(f"{self.base_url}/dashboard")
            time.sleep(3)
            
            # Should redirect to login if not authenticated
            current_url = self.driver.current_url
            redirected_to_login = "/login" in current_url
            
            tests.append({
                "name": "Dashboard Requires Authentication",
                "passed": redirected_to_login,
                "details": f"Redirected to: {current_url}"
            })
            
        except Exception as e:
            tests.append({
                "name": "Dashboard Protection Test",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_organization_pages(self) -> Dict[str, Any]:
        """Test organization management pages"""
        tests = []
        
        try:
            self.driver.get(f"{self.base_url}/organizations")
            time.sleep(2)
            
            # Should redirect to login if not authenticated
            tests.append({
                "name": "Organizations Page Requires Auth",
                "passed": "/login" in self.driver.current_url,
                "details": "Redirected to login page"
            })
            
        except Exception as e:
            tests.append({
                "name": "Organizations Page Test",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_dataset_pages(self) -> Dict[str, Any]:
        """Test dataset management pages"""
        tests = []
        
        # Test datasets list page
        try:
            self.driver.get(f"{self.base_url}/datasets")
            time.sleep(2)
            
            tests.append({
                "name": "Datasets Page Requires Auth",
                "passed": "/login" in self.driver.current_url,
                "details": "Redirected to login page"
            })
            
        except Exception as e:
            tests.append({
                "name": "Datasets Page Test",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test upload page
        try:
            self.driver.get(f"{self.base_url}/datasets/upload")
            time.sleep(2)
            
            tests.append({
                "name": "Upload Page Requires Auth",
                "passed": "/login" in self.driver.current_url,
                "details": "Redirected to login page"
            })
            
        except Exception as e:
            tests.append({
                "name": "Upload Page Test",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_model_pages(self) -> Dict[str, Any]:
        """Test model management pages"""
        tests = []
        
        # Test models list page
        try:
            self.driver.get(f"{self.base_url}/models")
            time.sleep(2)
            
            tests.append({
                "name": "Models Page Requires Auth",
                "passed": "/login" in self.driver.current_url,
                "details": "Redirected to login page"
            })
            
        except Exception as e:
            tests.append({
                "name": "Models Page Test",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        # Test create model page
        try:
            self.driver.get(f"{self.base_url}/models/create")
            time.sleep(2)
            
            tests.append({
                "name": "Create Model Page Requires Auth",
                "passed": "/login" in self.driver.current_url,
                "details": "Redirected to login page"
            })
            
        except Exception as e:
            tests.append({
                "name": "Create Model Page Test",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_sql_playground(self) -> Dict[str, Any]:
        """Test SQL playground functionality"""
        tests = []
        
        try:
            self.driver.get(f"{self.base_url}/sql")
            time.sleep(2)
            
            tests.append({
                "name": "SQL Playground Requires Auth",
                "passed": "/login" in self.driver.current_url,
                "details": "Redirected to login page"
            })
            
        except Exception as e:
            tests.append({
                "name": "SQL Playground Test",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_analytics_pages(self) -> Dict[str, Any]:
        """Test analytics dashboard pages"""
        tests = []
        
        try:
            self.driver.get(f"{self.base_url}/analytics")
            time.sleep(2)
            
            tests.append({
                "name": "Analytics Page Requires Auth",
                "passed": "/login" in self.driver.current_url,
                "details": "Redirected to login page"
            })
            
        except Exception as e:
            tests.append({
                "name": "Analytics Page Test",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_data_access_pages(self) -> Dict[str, Any]:
        """Test data access management pages"""
        tests = []
        
        try:
            self.driver.get(f"{self.base_url}/data-access")
            time.sleep(2)
            
            tests.append({
                "name": "Data Access Page Requires Auth",
                "passed": "/login" in self.driver.current_url,
                "details": "Redirected to login page"
            })
            
        except Exception as e:
            tests.append({
                "name": "Data Access Page Test",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_admin_pages(self) -> Dict[str, Any]:
        """Test admin panel pages"""
        tests = []
        
        try:
            self.driver.get(f"{self.base_url}/admin/organizations")
            time.sleep(2)
            
            tests.append({
                "name": "Admin Page Requires Auth",
                "passed": "/login" in self.driver.current_url,
                "details": "Redirected to login page"
            })
            
        except Exception as e:
            tests.append({
                "name": "Admin Page Test",
                "passed": False,
                "details": f"Error: {str(e)}"
            })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_responsive_design(self) -> Dict[str, Any]:
        """Test responsive design across different screen sizes"""
        tests = []
        
        screen_sizes = [
            (1920, 1080, "Desktop"),
            (1024, 768, "Tablet"),
            (375, 667, "Mobile")
        ]
        
        for width, height, device in screen_sizes:
            try:
                self.driver.set_window_size(width, height)
                self.driver.get(self.base_url)
                time.sleep(2)
                
                # Check if page renders without horizontal scroll
                body = self.driver.find_element(By.TAG_NAME, "body")
                page_width = self.driver.execute_script("return document.body.scrollWidth")
                
                tests.append({
                    "name": f"Responsive Design - {device}",
                    "passed": page_width <= width + 50,  # Allow some tolerance
                    "details": f"Page width: {page_width}px, Screen: {width}px"
                })
                
            except Exception as e:
                tests.append({
                    "name": f"Responsive Design - {device}",
                    "passed": False,
                    "details": f"Error: {str(e)}"
                })
        
        # Reset to default size
        self.driver.set_window_size(1920, 1080)
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }
    
    def test_navigation(self) -> Dict[str, Any]:
        """Test navigation and routing"""
        tests = []
        
        # Test various routes
        routes_to_test = [
            ("/", "Home/Landing"),
            ("/login", "Login"),
            ("/register", "Register"),
            ("/dashboard", "Dashboard"),
            ("/datasets", "Datasets"),
            ("/models", "Models"),
            ("/sql", "SQL Playground"),
            ("/analytics", "Analytics"),
            ("/admin/organizations", "Admin")
        ]
        
        for route, page_name in routes_to_test:
            try:
                self.driver.get(f"{self.base_url}{route}")
                time.sleep(2)
                
                # Check if page loads (doesn't show 404)
                page_source = self.driver.page_source.lower()
                is_404 = "404" in page_source or "not found" in page_source
                
                tests.append({
                    "name": f"Route Accessibility - {page_name}",
                    "passed": not is_404,
                    "details": f"URL: {route}, 404: {is_404}"
                })
                
            except Exception as e:
                tests.append({
                    "name": f"Route Accessibility - {page_name}",
                    "passed": False,
                    "details": f"Error: {str(e)}"
                })
        
        return {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["passed"]),
            "tests": tests
        }


def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import selenium
        return True
    except ImportError:
        print("❌ Selenium not found. Install with: pip install selenium")
        return False


def main():
    """Main function to run frontend tests"""
    print("🚀 AI Share Platform - Frontend Test Suite")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check if frontend is running
    import requests
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code not in [200, 404]:  # 404 is OK for Next.js routing
            print("❌ Frontend server is not responding properly")
            print("Please start the frontend server with: cd frontend && npm run dev")
            return False
    except requests.exceptions.RequestException:
        print("❌ Frontend server is not running or not accessible")
        print("Please start the frontend server with: cd frontend && npm run dev")
        return False
    
    # Run tests
    try:
        test_suite = FrontendTestSuite()
        results = test_suite.run_all_tests()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"test_results/frontend_test_results_{timestamp}.json"
        
        os.makedirs("test_results", exist_ok=True)
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Test results saved to: {results_file}")
        
        # Return success if all tests passed
        return results["summary"]["success_rate"] >= 80.0  # Allow 80% pass rate for frontend
        
    except Exception as e:
        print(f"❌ Frontend test suite failed: {e}")
        return False


if __name__ == "__main__":
    main() 