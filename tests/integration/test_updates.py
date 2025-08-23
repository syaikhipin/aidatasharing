#!/usr/bin/env python3
"""
Test script for updated file preview functionality
"""
import json

# Test the login functionality
def test_login():
    import requests
    
    print("🔐 Testing login functionality...")
    
    # Test admin login
    login_data = {
        'username': 'admin@example.com',
        'password': 'admin123'
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/api/auth/login',
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Admin login successful! Token: {token_data['access_token'][:20]}...")
            return token_data['access_token']
        else:
            print(f"❌ Admin login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login test error: {e}")
        return None

# Test file upload and preview
def test_file_preview(token):
    import requests
    import tempfile
    import os
    
    if not token:
        print("❌ Cannot test file preview without valid token")
        return
    
    print("\n📁 Testing file preview functionality...")
    
    # Create test files
    test_files = []
    
    # CSV file
    csv_content = """name,age,city,salary
John Doe,30,New York,75000
Jane Smith,25,Los Angeles,65000
Bob Johnson,35,Chicago,80000
Alice Brown,28,Houston,70000"""
    
    csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    csv_file.write(csv_content)
    csv_file.close()
    test_files.append(('CSV', csv_file.name))
    
    # JSON file
    json_content = {
        "users": [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
        ],
        "metadata": {
            "total": 2,
            "created": "2024-01-01"
        }
    }
    
    json_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(json_content, json_file, indent=2)
    json_file.close()
    test_files.append(('JSON', json_file.name))
    
    # Test each file
    for file_type, file_path in test_files:
        try:
            print(f"\n📄 Testing {file_type} file upload and preview...")
            
            # Upload file
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'text/plain')}
                headers = {'Authorization': f'Bearer {token}'}
                
                response = requests.post(
                    'http://localhost:8000/api/file-handler/upload',
                    files=files,
                    headers=headers
                )
                
                if response.status_code == 200:
                    upload_result = response.json()
                    print(f"✅ {file_type} upload successful!")
                    
                    # Test preview generation
                    file_id = upload_result.get('file_id')
                    if file_id:
                        preview_response = requests.get(
                            f'http://localhost:8000/api/file-handler/{file_id}/preview?preview_type=content',
                            headers=headers
                        )
                        
                        if preview_response.status_code == 200:
                            preview_data = preview_response.json()
                            print(f"✅ {file_type} preview generated successfully!")
                            print(f"   - MindsDB Compatible: {preview_data.get('mindsdb_compatible', False)}")
                            print(f"   - Format: {preview_data.get('format', 'Unknown')}")
                            print(f"   - Preview Type: {preview_data.get('preview_type', 'Unknown')}")
                            
                            if 'columns' in preview_data:
                                print(f"   - Columns: {len(preview_data['columns'])}")
                            if 'sample_data' in preview_data:
                                print(f"   - Sample Rows: {len(preview_data['sample_data'])}")
                        else:
                            print(f"❌ {file_type} preview failed: {preview_response.status_code}")
                else:
                    print(f"❌ {file_type} upload failed: {response.status_code} - {response.text}")
                    
        except Exception as e:
            print(f"❌ Error testing {file_type}: {e}")
        finally:
            # Clean up temp file
            if os.path.exists(file_path):
                os.unlink(file_path)

if __name__ == "__main__":
    print("🚀 Testing AI Share Platform Updates...")
    print("=" * 50)
    
    # Test login
    token = test_login()
    
    # Test file preview
    test_file_preview(token)
    
    print("\n" + "=" * 50)
    print("✅ Testing completed!")