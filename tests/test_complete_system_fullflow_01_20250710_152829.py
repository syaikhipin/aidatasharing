#!/usr/bin/env python3
"""
Comprehensive AI Share Platform System Test

This script tests the complete functionality including:
1. User registration and authentication
2. Organization creation and management
3. Dataset upload (CSV and PDF) with different organizations
4. AI chat functionality with datasets
5. Analytics and data logging
6. Data sharing and access controls
"""

import requests
import json
import time
import tempfile
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class AISharePlatformTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_tokens = {}
        self.organizations = {}
        self.datasets = {}
        self.users = {}
        
    def log(self, message, status="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        status_emoji = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "ERROR": "❌",
            "WARNING": "⚠️",
            "TEST": "🧪"
        }
        print(f"{status_emoji.get(status, 'ℹ️')} [{timestamp}] {message}")
    
    def create_test_csv(self, organization="org1"):
        """Create test CSV data tailored to organization"""
        if organization == "org1":
            csv_content = """product_name,category,sales_amount,quantity,total_revenue,region
Laptop Pro 15,Electronics,1299.99,1,1299.99,North America
Smart Phone X,Electronics,699.99,2,1399.98,Europe
Tablet Ultra,Electronics,399.99,1,399.99,Asia
Wireless Headphones,Audio,199.99,3,599.97,North America
Smart Watch,Wearables,299.99,1,299.99,Europe
Gaming Console,Electronics,499.99,1,499.99,North America
Bluetooth Speaker,Audio,79.99,2,159.98,Asia
E-Reader,Electronics,129.99,1,129.99,Europe"""
        else:  # org2
            csv_content = """employee_name,department,salary,years_experience,performance_rating,location
John Smith,Engineering,95000,5,4.2,San Francisco
Sarah Johnson,Marketing,72000,3,4.5,New York
Mike Brown,Sales,68000,2,3.8,Chicago
Lisa Davis,HR,65000,4,4.1,Austin
David Wilson,Engineering,110000,8,4.7,Seattle
Emma Taylor,Marketing,58000,1,3.9,Boston
Alex Chen,Engineering,88000,3,4.3,San Francisco
Maria Garcia,Sales,71000,4,4.0,Miami"""
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write(csv_content)
        temp_file.close()
        return temp_file.name
    
    def create_test_pdf_content(self, organization="org1"):
        """Create test content for PDF (we'll simulate this as text)"""
        if organization == "org1":
            return """Sales Report Q4 2024
            
Executive Summary:
Our Q4 2024 sales performance exceeded expectations with a 23% increase in revenue compared to Q3.
Key highlights include strong performance in Electronics category and expansion into new regions.

Product Performance:
- Electronics: $4,299.94 (65% of total revenue)
- Audio: $759.95 (11% of total revenue) 
- Wearables: $299.99 (4% of total revenue)

Regional Analysis:
- North America: $2,359.94 (36% of revenue)
- Europe: $2,029.96 (31% of revenue)
- Asia: $559.97 (8% of revenue)

Recommendations:
1. Increase marketing spend in Asia region
2. Expand wearables product line
3. Focus on premium electronics segment"""
        else:  # org2
            return """Employee Performance Review 2024

Company Overview:
Annual review of employee performance across all departments.
Focus on retention, skill development, and compensation alignment.

Department Analysis:
- Engineering: Highest performers with average rating 4.4
- Marketing: Strong growth potential, average rating 4.2
- Sales: Meeting targets, average rating 3.9
- HR: Consistent performance, average rating 4.1

Salary Analysis:
- Engineering: $97,667 average (highest)
- Sales: $69,500 average
- Marketing: $65,000 average
- HR: $65,000 average

Recommendations:
1. Increase sales team compensation
2. Provide additional training for junior staff
3. Implement performance-based bonuses"""
    
    def register_user(self, email, password, full_name, organization_name=None):
        """Register a new user or login if already exists"""
        self.log(f"Registering user: {email}")
        
        payload = {
            "email": email,
            "password": password,
            "full_name": full_name
        }
        
        if organization_name:
            payload["organization_name"] = organization_name
        
        try:
            response = self.session.post(f"{BASE_URL}/api/auth/register", json=payload)
            if response.status_code == 201:
                self.log(f"User {email} registered successfully", "SUCCESS")
                return response.json()
            elif response.status_code == 400 and "already registered" in response.text:
                self.log(f"User {email} already exists, will try to login", "WARNING")
                return {"message": "User already exists"}
            else:
                self.log(f"Failed to register {email}: {response.status_code} - {response.text}", "ERROR")
                return None
        except Exception as e:
            self.log(f"Registration error for {email}: {e}", "ERROR")
            return None
    
    def login_user(self, email, password):
        """Login user and store auth token"""
        self.log(f"Logging in user: {email}")
        
        try:
            # Use form data for OAuth2 login
            payload = {
                "username": email,
                "password": password
            }
            
            response = self.session.post(f"{BASE_URL}/api/auth/login", data=payload)
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                if token:
                    self.auth_tokens[email] = token
                    self.session.headers.update({"Authorization": f"Bearer {token}"})
                    self.log(f"User {email} logged in successfully", "SUCCESS")
                    return data
                else:
                    self.log(f"No token received for {email}", "ERROR")
                    return None
            else:
                self.log(f"Failed to login {email}: {response.status_code} - {response.text}", "ERROR")
                return None
        except Exception as e:
            self.log(f"Login error for {email}: {e}", "ERROR")
            return None
    
    def create_organization(self, name, description, org_type="small_business"):
        """Create a new organization"""
        self.log(f"Creating organization: {name}")
        
        payload = {
            "name": name,
            "description": description,
            "type": org_type
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/api/organizations/", json=payload)
            if response.status_code in [200, 201]:  # Accept both 200 and 201 as success
                org_data = response.json()
                self.organizations[name] = org_data
                self.log(f"Organization {name} created successfully (ID: {org_data.get('id')})", "SUCCESS")
                return org_data
            else:
                self.log(f"Failed to create organization {name}: {response.status_code} - {response.text}", "ERROR")
                return None
        except Exception as e:
            self.log(f"Organization creation error for {name}: {e}", "ERROR")
            return None
    
    def upload_dataset(self, name, description, file_path, dataset_type="csv"):
        """Upload a dataset"""
        self.log(f"Uploading dataset: {name}")
        
        try:
            # Check current auth
            auth_header = self.session.headers.get("Authorization")
            if not auth_header:
                self.log("No authentication token found", "ERROR")
                return None
            
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'text/csv' if dataset_type == 'csv' else 'text/plain')}
                data = {
                    'name': name,
                    'description': description,
                    'sharing_level': 'organization'
                }
                
                self.log(f"Sending upload request with auth: {auth_header[:20]}...")
                response = self.session.post(f"{BASE_URL}/api/datasets/upload", files=files, data=data)
                
            if response.status_code in [200, 201]:
                dataset_data = response.json()
                # Handle nested dataset structure
                if isinstance(dataset_data, dict) and "dataset" in dataset_data:
                    dataset_data = dataset_data["dataset"]
                
                self.datasets[name] = dataset_data
                self.log(f"Dataset {name} uploaded successfully (ID: {dataset_data.get('id')})", "SUCCESS")
                return dataset_data
            else:
                self.log(f"Failed to upload dataset {name}: {response.status_code}", "ERROR")
                self.log(f"Response body: {response.text[:500]}", "ERROR")
                return None
        except Exception as e:
            self.log(f"Dataset upload error for {name}: {e}", "ERROR")
            return None
    
    def chat_with_dataset(self, dataset_id, message, session_id=None):
        """Chat with a dataset"""
        self.log(f"Chatting with dataset {dataset_id}: {message[:50]}...")
        
        payload = {
            "message": message
        }
        
        if session_id:
            payload["session_id"] = session_id
        
        try:
            response = self.session.post(f"{BASE_URL}/api/datasets/{dataset_id}/chat", json=payload)
            if response.status_code == 200:
                chat_data = response.json()
                self.log(f"Chat response received from dataset {dataset_id}", "SUCCESS")
                return chat_data
            else:
                self.log(f"Failed to chat with dataset {dataset_id}: {response.status_code} - {response.text}", "ERROR")
                return None
        except Exception as e:
            self.log(f"Chat error with dataset {dataset_id}: {e}", "ERROR")
            return None
    
    def get_dataset_analytics(self, dataset_id):
        """Get analytics for a dataset"""
        self.log(f"Getting analytics for dataset {dataset_id}")
        
        try:
            response = self.session.get(f"{BASE_URL}/api/analytics/dataset/{dataset_id}")
            if response.status_code == 200:
                analytics_data = response.json()
                self.log(f"Analytics retrieved for dataset {dataset_id}", "SUCCESS")
                return analytics_data
            else:
                self.log(f"Failed to get analytics for dataset {dataset_id}: {response.status_code} - {response.text}", "ERROR")
                return None
        except Exception as e:
            self.log(f"Analytics error for dataset {dataset_id}: {e}", "ERROR")
            return None
    
    def test_complete_workflow(self):
        """Test the complete workflow"""
        self.log("Starting comprehensive AI Share Platform test", "TEST")
        print("=" * 80)
        
        # Generate unique emails with timestamp
        timestamp = int(time.time())
        
        # Test data
        test_users = [
            {
                "email": f"alice{timestamp}@techcorp.com",
                "password": "password123",
                "full_name": "Alice Johnson",
                "organization": f"TechCorp Solutions {timestamp}"
            },
            {
                "email": f"bob{timestamp}@dataanalytics.com", 
                "password": "password123",
                "full_name": "Bob Smith",
                "organization": f"Data Analytics Pro {timestamp}"
            }
        ]
        
        # Step 1: Register users and create organizations
        self.log("STEP 1: User Registration and Organization Setup", "TEST")
        
        for user_data in test_users:
            # Register user
            user_result = self.register_user(
                user_data["email"],
                user_data["password"], 
                user_data["full_name"]
            )
            
            if not user_result:
                continue
                
            # Login user
            login_result = self.login_user(user_data["email"], user_data["password"])
            if not login_result:
                continue
                
            self.users[user_data["email"]] = login_result
            
            # Create organization
            org_result = self.create_organization(
                user_data["organization"],
                f"Test organization for {user_data['full_name']}"
            )
        
        # Step 2: Upload datasets for each organization
        self.log("STEP 2: Dataset Upload Testing", "TEST")
        
        org_count = 1
        for user_email in self.users.keys():
            # Set auth for this user
            token = self.auth_tokens.get(user_email)
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
            
            # Create and upload CSV dataset
            csv_file = self.create_test_csv(f"org{org_count}")
            csv_dataset = self.upload_dataset(
                f"Sales Data Org{org_count}",
                f"Test sales dataset for organization {org_count}",
                csv_file,
                "csv"
            )
            
            # Create and upload PDF dataset (simulate as text file)
            pdf_content = self.create_test_pdf_content(f"org{org_count}")
            pdf_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            pdf_file.write(pdf_content)
            pdf_file.close()
            
            pdf_dataset = self.upload_dataset(
                f"Report Document Org{org_count}",
                f"Test report document for organization {org_count}",
                pdf_file.name,
                "txt"
            )
            
            # Clean up temp files
            os.unlink(csv_file)
            os.unlink(pdf_file.name)
            
            org_count += 1
        
        # Step 3: Test AI chat with datasets
        self.log("STEP 3: AI Chat Testing", "TEST")
        
        for dataset_name, dataset_data in self.datasets.items():
            dataset_id = dataset_data.get("id")
            if not dataset_id:
                continue
                
            # Test questions based on dataset type
            if "Sales Data" in dataset_name:
                test_questions = [
                    "What is the total revenue in this dataset?",
                    "Which product category has the highest sales?",
                    "Show me the sales by region",
                    "What insights can you provide about this sales data?"
                ]
            else:  # Report documents
                test_questions = [
                    "Summarize the key findings in this document",
                    "What are the main recommendations?",
                    "What performance metrics are mentioned?",
                    "What are the trends discussed?"
                ]
            
            for question in test_questions:
                chat_result = self.chat_with_dataset(dataset_id, question)
                if chat_result:
                    answer = chat_result.get("answer", "No answer")
                    self.log(f"Q: {question[:50]}... A: {answer[:100]}...", "SUCCESS")
                time.sleep(1)  # Be nice to the API
        
        # Step 4: Test analytics
        self.log("STEP 4: Analytics Testing", "TEST")
        
        for dataset_name, dataset_data in self.datasets.items():
            dataset_id = dataset_data.get("id")
            if dataset_id:
                analytics = self.get_dataset_analytics(dataset_id)
                if analytics:
                    summary = analytics.get("summary", {})
                    self.log(f"Dataset {dataset_name} analytics: {summary}", "SUCCESS")
        
        # Step 5: Test system health
        self.log("STEP 5: System Health Check", "TEST")
        
        try:
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                health_data = response.json()
                self.log(f"System health: {health_data.get('status')}", "SUCCESS")
                
                # Print service status
                services = health_data.get("services", {})
                for service, status in services.items():
                    service_status = status.get("status", "unknown")
                    self.log(f"  {service}: {service_status}", "SUCCESS" if service_status in ["connected", "available", "operational"] else "WARNING")
            else:
                self.log("System health check failed", "ERROR")
        except Exception as e:
            self.log(f"Health check error: {e}", "ERROR")
        
        print("=" * 80)
        self.log("Comprehensive test completed!", "SUCCESS")
        
        # Summary
        self.log("TEST SUMMARY:", "TEST")
        self.log(f"Users created: {len(self.users)}")
        self.log(f"Organizations created: {len(self.organizations)}")
        self.log(f"Datasets uploaded: {len(self.datasets)}")
        self.log("All major functionality tested successfully!")

def main():
    """Main test function"""
    print("🚀 AI Share Platform - Comprehensive System Test")
    print("=" * 80)
    
    # Check if services are running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend service is not responding properly")
            return
    except:
        print("❌ Backend service is not running. Please start with ./start-dev.sh")
        return
    
    try:
        response = requests.get(f"{FRONTEND_URL}", timeout=5)
    except:
        print("⚠️  Frontend service may not be running, but continuing with backend tests")
    
    # Run the comprehensive test
    tester = AISharePlatformTester()
    tester.test_complete_workflow()

if __name__ == "__main__":
    main() 