#!/usr/bin/env python3
"""
Test MindsDB connection and chat functionality
"""
import requests
import json
import time

def test_mindsdb_direct():
    """Test direct MindsDB connection"""
    
    print("Testing Direct MindsDB Connection...")
    print("="*40)
    
    try:
        # Test MindsDB health endpoint
        mindsdb_url = "http://localhost:47334"
        
        print(f"Testing MindsDB at {mindsdb_url}")
        
        # Check if MindsDB is running
        health_response = requests.get(f"{mindsdb_url}/api/status", timeout=10)
        
        if health_response.status_code == 200:
            print("✅ MindsDB is running!")
            print(f"Status: {health_response.json()}")
            return True
        else:
            print(f"❌ MindsDB health check failed: {health_response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to MindsDB - is it running?")
        return False
    except Exception as e:
        print(f"❌ Error testing MindsDB: {e}")
        return False

def test_mindsdb_via_backend():
    """Test MindsDB functionality via backend API"""
    
    print("\n" + "="*50)
    print("Testing MindsDB via Backend API")
    print("="*50)
    
    backend_url = "http://localhost:8000"
    
    # Login credentials
    login_data = {
        "username": "alice@techcorp.com",
        "password": "Password123!"
    }
    
    try:
        # Login
        print("Logging in...")
        login_response = requests.post(f"{backend_url}/api/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
            
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful!")
        
        # Get datasets
        print("Getting datasets...")
        datasets_response = requests.get(f"{backend_url}/api/datasets/", headers=headers)
        
        if datasets_response.status_code != 200:
            print(f"❌ Failed to get datasets: {datasets_response.status_code}")
            return False
            
        datasets = datasets_response.json()
        print(f"✅ Found {len(datasets)} datasets")
        
        if not datasets:
            print("❌ No datasets found to test with")
            return False
            
        # Use the first dataset for testing
        test_dataset = datasets[0]
        dataset_id = test_dataset.get('id')
        dataset_name = test_dataset.get('name', 'Unknown')
        
        print(f"Testing with dataset: {dataset_name} (ID: {dataset_id})")
        
        # Test chat functionality
        print("Testing chat functionality...")
        
        chat_data = {
            "message": "What is this dataset about? Give me a brief summary.",
            "dataset_id": dataset_id
        }
        
        chat_response = requests.post(
            f"{backend_url}/api/datasets/{dataset_id}/chat",
            json=chat_data,
            headers=headers,
            timeout=30
        )
        
        if chat_response.status_code == 200:
            response_data = chat_response.json()
            print("✅ Chat functionality working!")
            print(f"Response: {response_data.get('response', 'No response')}")
            return True
        else:
            print(f"❌ Chat failed: {chat_response.status_code}")
            print(f"Error: {chat_response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Chat request timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing MindsDB via backend: {e}")
        return False

def test_mindsdb_models():
    """Test MindsDB models directly"""
    
    print("\n" + "="*50)
    print("Testing MindsDB Models")
    print("="*50)
    
    try:
        mindsdb_url = "http://localhost:47334"
        
        # List available models/databases
        print("Getting MindsDB databases...")
        databases_response = requests.get(f"{mindsdb_url}/api/databases", timeout=10)
        
        if databases_response.status_code == 200:
            databases = databases_response.json()
            print(f"✅ Found {len(databases)} databases:")
            for db in databases:
                print(f"  - {db.get('name', 'Unknown')}")
        else:
            print(f"❌ Failed to get databases: {databases_response.status_code}")
            
        # Test a simple query
        print("\nTesting simple query...")
        query_data = {
            "query": "SHOW DATABASES;"
        }
        
        query_response = requests.post(
            f"{mindsdb_url}/api/sql/query",
            json=query_data,
            timeout=15
        )
        
        if query_response.status_code == 200:
            print("✅ Query executed successfully!")
            result = query_response.json()
            print(f"Query result: {result}")
            return True
        else:
            print(f"❌ Query failed: {query_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing MindsDB models: {e}")
        return False

if __name__ == "__main__":
    print("MindsDB Connection Test")
    print("=======================")
    
    # Test direct MindsDB connection
    direct_result = test_mindsdb_direct()
    
    # Test MindsDB models
    models_result = test_mindsdb_models()
    
    # Test via backend API
    backend_result = test_mindsdb_via_backend()
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Direct MindsDB Connection: {'✅ PASS' if direct_result else '❌ FAIL'}")
    print(f"MindsDB Models Test: {'✅ PASS' if models_result else '❌ FAIL'}")
    print(f"Backend API Chat Test: {'✅ PASS' if backend_result else '❌ FAIL'}")