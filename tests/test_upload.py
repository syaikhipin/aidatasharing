#!/usr/bin/env python3
"""
Test script for file upload functionality
"""
import requests
import json

def test_file_upload():
    print("🧪 Testing AI Share Platform File Upload Functionality")
    print("=" * 60)
    
    # Test if backend is responsive
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        print(f"✅ Backend is responsive: {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Backend not accessible: {e}")
        return
    
    # Test creating a user first (to get auth token)
    print("\n📝 Testing user registration...")
    
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/register",
            json=user_data,
            timeout=10
        )
        print(f"📤 Registration response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"✅ Got auth token: {token[:20]}...")
            
            # Test file upload
            print("\n📁 Testing file upload...")
            
            files = {'file': ('test.csv', 'Name,Age\nJohn,30\nJane,25', 'text/csv')}
            form_data = {
                'dataset_name': 'Test CSV Dataset',
                'description': 'Test upload',
                'sharing_level': 'PRIVATE',
                'process_with_ai': 'false'
            }
            
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.post(
                "http://localhost:8000/api/files/upload/universal",
                files=files,
                data=form_data,
                headers=headers,
                timeout=30
            )
            
            print(f"📤 Upload response: {response.status_code}")
            print(f"📄 Response body: {response.text[:500]}")
            
            if response.status_code == 200:
                upload_data = response.json()
                file_upload_id = upload_data.get('file_upload_id')
                
                if file_upload_id:
                    print(f"✅ File uploaded successfully: ID {file_upload_id}")
                    
                    # Test preview
                    print(f"\n👁️  Testing file preview for ID {file_upload_id}...")
                    
                    response = requests.get(
                        f"http://localhost:8000/api/files/uploads/{file_upload_id}/preview",
                        headers=headers,
                        timeout=15
                    )
                    
                    print(f"📤 Preview response: {response.status_code}")
                    print(f"📄 Preview data: {response.text[:300]}")
                    
                    if response.status_code == 200:
                        print("✅ Preview generation successful!")
                    else:
                        print(f"❌ Preview failed: {response.text}")
                else:
                    print("❌ No file upload ID returned")
            else:
                print(f"❌ Upload failed: {response.text}")
                
        else:
            print(f"❌ Registration failed: {response.text}")
            
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_file_upload()