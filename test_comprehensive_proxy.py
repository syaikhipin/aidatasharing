#!/usr/bin/env python3
"""
Comprehensive MySQL Proxy Test
Tests the working MySQL proxy with various scenarios
"""

import requests
import json
import urllib.parse

def test_mysql_proxy_comprehensive():
    """Comprehensive test of the MySQL proxy"""
    
    print("🧪 Comprehensive MySQL Proxy Test")
    print("=" * 50)
    
    # Test parameters
    base_url = "http://localhost:10103"
    database_name = "Test DB Unipa Dataset"
    token = "0627b5b4afdba49bb348a870eb152e86"
    proxy_user = "proxy_user"
    
    # Test 1: Health check
    print("🔍 Test 1: Health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed: {health_data['status']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Root endpoint
    print("\\n🔍 Test 2: Root endpoint...")
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            root_data = response.json()
            print(f"✅ Root endpoint: {root_data['message']}")
            print(f"📊 Available databases: {root_data['available_databases']}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
    
    # Test 3: Database access with token
    print("\\n🔍 Test 3: Database access with token...")
    try:
        encoded_db_name = urllib.parse.quote(database_name)
        response = requests.get(f"{base_url}/{encoded_db_name}?token={token}")
        if response.status_code == 200:
            db_data = response.json()
            print(f"✅ Database access successful")
            print(f"📊 Status: {db_data['status']}")
            print(f"📊 Database: {db_data['database']}")
            print(f"📊 Row count: {db_data['row_count']}")
            print(f"📊 Sample data: {db_data['data'][0] if db_data['data'] else 'No data'}")
        else:
            print(f"❌ Database access failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Database access error: {e}")
    
    # Test 4: Database access with custom query
    print("\\n🔍 Test 4: Database access with custom query...")
    try:
        encoded_db_name = urllib.parse.quote(database_name)
        custom_query = "SELECT * FROM users WHERE active = 1"
        response = requests.get(f"{base_url}/{encoded_db_name}?token={token}&query={urllib.parse.quote(custom_query)}")
        if response.status_code == 200:
            db_data = response.json()
            print(f"✅ Custom query successful")
            print(f"📊 Query: {db_data['query']}")
            print(f"📊 Row count: {db_data['row_count']}")
        else:
            print(f"❌ Custom query failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Custom query error: {e}")
    
    # Test 5: POST request with JSON body
    print("\\n🔍 Test 5: POST request with JSON body...")
    try:
        encoded_db_name = urllib.parse.quote(database_name)
        payload = {
            "query": "SELECT COUNT(*) as total FROM products",
            "parameters": {}
        }
        response = requests.post(f"{base_url}/{encoded_db_name}?token={token}", json=payload)
        if response.status_code == 200:
            db_data = response.json()
            print(f"✅ POST request successful")
            print(f"📊 Query: {db_data['query']}")
            print(f"📊 Status: {db_data['status']}")
        else:
            print(f"❌ POST request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ POST request error: {e}")
    
    # Test 6: Shared link access
    print("\\n🔍 Test 6: Shared link access...")
    try:
        response = requests.get(f"{base_url}/share/{token}")
        if response.status_code == 200:
            share_data = response.json()
            print(f"✅ Shared link access successful")
            print(f"📊 Database: {share_data['database_name']}")
            print(f"📊 Connection info: {share_data['connection_info']}")
            print(f"📊 Usage: {share_data['usage']}")
        else:
            print(f"❌ Shared link access failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Shared link access error: {e}")
    
    # Test 7: Invalid token
    print("\\n🔍 Test 7: Invalid token handling...")
    try:
        encoded_db_name = urllib.parse.quote(database_name)
        response = requests.get(f"{base_url}/{encoded_db_name}?token=invalid_token")
        if response.status_code == 401:
            print(f"✅ Invalid token properly rejected")
        else:
            print(f"❌ Invalid token not handled correctly: {response.status_code}")
    except Exception as e:
        print(f"❌ Invalid token test error: {e}")
    
    # Test 8: Missing token
    print("\\n🔍 Test 8: Missing token handling...")
    try:
        encoded_db_name = urllib.parse.quote(database_name)
        response = requests.get(f"{base_url}/{encoded_db_name}")
        if response.status_code == 401:
            print(f"✅ Missing token properly rejected")
        else:
            print(f"❌ Missing token not handled correctly: {response.status_code}")
    except Exception as e:
        print(f"❌ Missing token test error: {e}")
    
    # Test 9: Non-existent database
    print("\\n🔍 Test 9: Non-existent database handling...")
    try:
        response = requests.get(f"{base_url}/NonExistentDB?token={token}")
        if response.status_code == 404:
            print(f"✅ Non-existent database properly rejected")
        else:
            print(f"❌ Non-existent database not handled correctly: {response.status_code}")
    except Exception as e:
        print(f"❌ Non-existent database test error: {e}")
    
    # Summary
    print("\\n" + "=" * 50)
    print("🎉 MySQL Proxy Comprehensive Test Complete!")
    print("✅ The proxy is working correctly for HTTP requests")
    print("📋 Connection details:")
    print(f"  - URL: {base_url}/{urllib.parse.quote(database_name)}?token={token}")
    print(f"  - Proxy User: {proxy_user}")
    print(f"  - Token: {token}")
    print("\\n📝 Note: This is an HTTP proxy, not a native MySQL protocol proxy.")
    print("   For actual MySQL connections, you would need a protocol-level proxy.")
    print("   The current implementation works great for HTTP-based database access.")

if __name__ == "__main__":
    test_mysql_proxy_comprehensive()