#!/usr/bin/env python3
"""
Test the environment variable update API endpoint
"""

import requests
import json
import sys

def test_environment_variables_api():
    """Test the environment variables API endpoints"""
    
    base_url = "http://localhost:8000"
    
    try:
        # Test GET /api/admin/environment-variables
        print("🧪 Testing GET /api/admin/environment-variables...")
        response = requests.get(f"{base_url}/api/admin/environment-variables")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ GET endpoint works!")
            print(f"  - Managed variables: {data.get('managed_count', 0)}")
            print(f"  - Unmanaged variables: {data.get('unmanaged_count', 0)}")
            print(f"  - Categories: {list(data.get('categories', {}).keys())}")
            
            # Find a managed variable to test update
            managed_vars = [v for v in data.get('variables', []) if v.get('is_managed', False)]
            if managed_vars:
                test_var = managed_vars[0]
                print(f"  - Found test variable: {test_var['name']}")
                
                # Test PUT /api/admin/unified-config/environment/{key}
                print(f"\\n🧪 Testing PUT /api/admin/unified-config/environment/{test_var['name']}...")
                
                new_value = "test_value_from_api"
                put_response = requests.put(
                    f"{base_url}/api/admin/unified-config/environment/{test_var['name']}",
                    json={"value": new_value}
                )
                
                if put_response.status_code == 200:
                    print("✅ PUT endpoint works!")
                    print(f"  - Response: {put_response.json()}")
                else:
                    print(f"❌ PUT endpoint failed: {put_response.status_code}")
                    print(f"  - Response: {put_response.text}")
            else:
                print("⚠️  No managed variables found to test update")
                
        else:
            print(f"❌ GET endpoint failed: {response.status_code}")
            print(f"  - Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Make sure it's running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Environment Variables API")
    print("=" * 50)
    
    success = test_environment_variables_api()
    
    if success:
        print("\\n🎉 API tests completed!")
    else:
        print("\\n❌ API tests failed!")
        sys.exit(1)