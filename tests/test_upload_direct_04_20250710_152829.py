#!/usr/bin/env python3
"""
Direct Upload Test for AI Share Platform

This script directly tests the upload functionality with detailed error reporting.
"""

import requests
import tempfile
import os
import json
import time

BASE_URL = "http://localhost:8000"

def test_upload():
    print("🧪 AI Share Platform - Direct Upload Test")
    print("=" * 60)
    
    # Step 1: Check if backend is running
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Backend is not healthy")
            return
        print("✅ Backend is healthy")
    except:
        print("❌ Backend is not accessible")
        return
    
    # Step 2: Register/Login user
    print("\n📝 Step 1: User Authentication")
    
    # Generate unique identifiers
    timestamp = int(time.time())
    
    # Try to register
    register_data = {
        "email": f"testuser{timestamp}@example.com",
        "password": "password123",
        "full_name": "Test User"
    }
    
    register_response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    print(f"Register response: {register_response.status_code}")
    
    # Login
    login_data = {
        "username": f"testuser{timestamp}@example.com",
        "password": "password123"
    }
    
    login_response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
        return
    
    token = login_response.json().get("access_token")
    if not token:
        print("❌ No access token received")
        return
    
    print(f"✅ Logged in successfully, token: {token[:20]}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 3: Create organization
    print("\n🏢 Step 2: Organization Creation")
    
    org_data = {
        "name": f"Test Organization {timestamp}",
        "description": "Test organization for upload testing",
        "type": "small_business"
    }
    
    org_response = requests.post(f"{BASE_URL}/api/organizations/", json=org_data, headers=headers)
    if org_response.status_code not in [200, 201]:
        print(f"❌ Organization creation failed: {org_response.status_code} - {org_response.text}")
        return
    
    org_info = org_response.json()
    print(f"✅ Organization created: {org_info.get('name')} (ID: {org_info.get('id')})")
    
    # Step 4: Test CSV upload
    print("\n📁 Step 3: CSV Upload Test")
    
    # Create test CSV
    csv_content = """product_name,category,price,quantity,total_sales
Laptop Pro,Electronics,1299.99,1,1299.99
Smartphone X,Electronics,699.99,2,1399.98
Tablet Ultra,Electronics,399.99,1,399.99
Wireless Headphones,Audio,199.99,3,599.97
Smart Watch,Wearables,299.99,1,299.99"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name
    
    try:
        # Upload CSV
        with open(csv_file_path, 'rb') as f:
            files = {'file': ('sales_data.csv', f, 'text/csv')}
            data = {
                'name': 'Sales Data Test',
                'description': 'Test sales dataset for AI chat functionality',
                'sharing_level': 'organization'
            }
            
            print(f"Uploading CSV file...")
            upload_response = requests.post(
                f"{BASE_URL}/api/datasets/upload",
                files=files,
                data=data,
                headers=headers
            )
        
        print(f"Upload status: {upload_response.status_code}")
        
        if upload_response.status_code in [200, 201]:
            response_data = upload_response.json()
            print("✅ CSV uploaded successfully!")
            
            # Handle nested response structure
            if isinstance(response_data, dict):
                if "dataset" in response_data:
                    dataset = response_data["dataset"]
                    dataset_id = dataset.get("id")
                else:
                    dataset = response_data
                    dataset_id = response_data.get("id")
                
                print(f"📊 Dataset ID: {dataset_id}")
                print(f"📝 Dataset Name: {dataset.get('name')}")
                print(f"🔢 Row Count: {dataset.get('row_count')}")
                print(f"📋 Column Count: {dataset.get('column_count')}")
                
                # Check AI features
                ai_features = response_data.get("ai_features", {})
                chat_available = response_data.get("ai_chat_available", False)
                
                print(f"🤖 AI Chat Available: {chat_available}")
                if ai_features:
                    print(f"🎯 Chat Enabled: {ai_features.get('chat_enabled')}")
                    print(f"⚙️ Model Ready: {ai_features.get('model_ready')}")
                
                # Step 5: Test AI Chat
                if dataset_id and chat_available:
                    print(f"\n💬 Step 4: AI Chat Test")
                    
                    test_questions = [
                        "What is the total revenue in this dataset?",
                        "Which product has the highest sales?",
                        "Show me the sales by category",
                        "What insights can you provide about this sales data?"
                    ]
                    
                    for question in test_questions:
                        print(f"\nQ: {question}")
                        
                        chat_data = {"message": question}
                        chat_response = requests.post(
                            f"{BASE_URL}/api/datasets/{dataset_id}/chat",
                            json=chat_data,
                            headers=headers
                        )
                        
                        if chat_response.status_code == 200:
                            chat_result = chat_response.json()
                            answer = chat_result.get("answer", "No answer provided")
                            print(f"A: {answer[:200]}{'...' if len(answer) > 200 else ''}")
                        else:
                            print(f"❌ Chat failed: {chat_response.status_code} - {chat_response.text[:200]}")
                
                # Step 6: Test Analytics
                print(f"\n📈 Step 5: Analytics Test")
                
                analytics_response = requests.get(
                    f"{BASE_URL}/api/analytics/dataset/{dataset_id}",
                    headers=headers
                )
                
                if analytics_response.status_code == 200:
                    analytics = analytics_response.json()
                    print("✅ Analytics retrieved successfully")
                    summary = analytics.get("summary", {})
                    print(f"📊 Access Count: {summary.get('access_count', 0)}")
                    print(f"💬 Chat Count: {summary.get('chat_count', 0)}")
                else:
                    print(f"⚠️ Analytics failed: {analytics_response.status_code}")
                
            else:
                print(f"⚠️ Unexpected response format: {response_data}")
                
        else:
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(f"Error details: {upload_response.text}")
            
            # Try to get more detailed error info
            try:
                error_data = upload_response.json()
                print(f"Structured error: {json.dumps(error_data, indent=2)}")
            except:
                print("Raw error response:", upload_response.text[:1000])
    
    finally:
        # Clean up
        if os.path.exists(csv_file_path):
            os.unlink(csv_file_path)
    
    print("\n" + "=" * 60)
    print("🎯 Upload test completed!")

if __name__ == "__main__":
    test_upload() 