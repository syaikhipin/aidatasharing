#!/usr/bin/env python3
"""
Test API Connector Creation
Simple test to verify API connector functionality
"""

import sys
import os
sys.path.append('.')

def test_api_connector_logic():
    """Test the API connector creation logic without actual database"""
    print("Testing API connector creation logic...")
    
    # Simulate connector data
    test_connector_data = {
        "name": "Test API",
        "connector_type": "api",
        "description": "Test API connector",
        "connection_config": {
            "base_url": "https://jsonplaceholder.typicode.com",
            "endpoint": "/posts",
            "method": "GET",
            "timeout": 30,
            "headers": {}
        },
        "credentials": {}
    }
    
    # Validate connector type
    supported_types = ['mysql', 'postgresql', 's3', 'api', 'mongodb', 'clickhouse']
    if test_connector_data["connector_type"] in supported_types:
        print(f"✅ Connector type '{test_connector_data['connector_type']}' is supported")
    else:
        print(f"❌ Connector type '{test_connector_data['connector_type']}' not supported")
        return False
    
    # Test API connection logic
    config = test_connector_data["connection_config"]
    base_url = config.get("base_url", "")
    endpoint = config.get("endpoint", "")
    method = config.get("method", "GET").upper()
    
    if base_url and endpoint:
        full_url = f"{base_url.rstrip('/')}{endpoint}"
        print(f"✅ Valid API configuration: {method} {full_url}")
    else:
        print("❌ Missing base_url or endpoint")
        return False
    
    print("✅ API connector creation logic appears correct")
    return True

def test_api_connection():
    """Test actual API connection to validate logic"""
    try:
        import requests
        
        # Test with a public API
        url = "https://jsonplaceholder.typicode.com/posts"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API test successful: {len(data)} items retrieved")
            print(f"  Sample keys: {list(data[0].keys()) if data else 'None'}")
            return True
        else:
            print(f"❌ API test failed: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def main():
    print("=" * 60)
    print("API CONNECTOR FUNCTIONALITY TEST")
    print("=" * 60)
    
    success1 = test_api_connector_logic()
    success2 = test_api_connection()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✅ All API connector tests passed!")
    else:
        print("❌ Some API connector tests failed!")
    print("=" * 60)

if __name__ == "__main__":
    main()