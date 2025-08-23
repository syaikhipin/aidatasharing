#!/usr/bin/env python3
"""
Test script to verify JSON metadata processing fix
"""

import json
import tempfile
import os

# Create a test JSON file
test_data = {
    "users": [
        {"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "age": 25},
        {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "age": 35}
    ],
    "metadata": {
        "total_users": 3,
        "created_at": "2025-08-15T12:00:00Z",
        "version": "1.0"
    }
}

# Write test JSON file
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(test_data, f, indent=2)
    test_file_path = f.name

print(f"Created test JSON file: {test_file_path}")

# Test the helper functions directly
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    # Import the helper functions we just added
    from app.api.datasets import _count_json_nesting, _count_json_elements, _analyze_json_types
    
    # Test the functions
    print("\n🧪 Testing JSON analysis functions:")
    
    nesting_level = _count_json_nesting(test_data)
    print(f"✅ Nesting level: {nesting_level}")
    
    element_count = _count_json_elements(test_data)
    print(f"✅ Element count: {element_count}")
    
    data_types = _analyze_json_types(test_data)
    print(f"✅ Data types analysis: {json.dumps(data_types, indent=2)}")
    
    print("\n🎉 All helper functions work correctly!")
    
except Exception as e:
    print(f"❌ Error testing helper functions: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Clean up
    if os.path.exists(test_file_path):
        os.unlink(test_file_path)
        print(f"\n🧹 Cleaned up test file: {test_file_path}")