#!/usr/bin/env python3
"""
Test script for admin endpoint
"""

import requests
import json
from datetime import datetime

def test_admin_endpoint():
    """Test the admin stats endpoint"""
    base_url = "http://localhost:8000"
    
    # Test admin stats endpoint
    try:
        response = requests.get(f"{base_url}/api/admin/stats")
        print(f"Admin stats endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Admin stats data:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Error response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Backend server is not running on port 8000")
    except Exception as e:
        print(f"Error testing admin endpoint: {e}")

if __name__ == "__main__":
    test_admin_endpoint()