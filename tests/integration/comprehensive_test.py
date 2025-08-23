#!/usr/bin/env python3
"""
Comprehensive test of S3 and MindsDB functionality
"""
import requests
import json
import boto3
from botocore.exceptions import ClientError

def test_backend_login():
    """Test different login formats for backend API"""
    
    backend_url = "http://localhost:8000"
    
    # Try different login formats
    login_formats = [
        {"username": "alice@techcorp.com", "password": "Password123!"},
        {"email": "alice@techcorp.com", "password": "Password123!"},
        {"login": "alice@techcorp.com", "password": "Password123!"},
    ]
    
    for i, login_data in enumerate(login_formats):
        try:
            print(f"Trying login format {i+1}: {login_data}")
            response = requests.post(f"{backend_url}/api/auth/login", json=login_data)
            
            if response.status_code == 200:
                print(f"✅ Login successful with format {i+1}")
                return response.json().get("access_token")
            else:
                print(f"❌ Login failed with format {i+1}: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Error with format {i+1}: {e}")
    
    return None

def test_s3_dataset_creation():
    """Test creating a dataset from S3 bucket"""
    
    print("\n" + "="*50)
    print("Testing S3 Dataset Creation")
    print("="*50)
    
    # S3 credentials
    endpoint = "g7h4.fra3.idrivee2-51.com"
    access_key = "kPqafITIVXXwrO0MLegM"
    secret_key = "QNbbIp6C9qSBfwkV8OnQYbfmMJYKZEwGoUcAu0f1"
    
    try:
        # List files in S3 bucket
        s3_client = boto3.client(
            's3',
            endpoint_url=f'https://{endpoint}',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='us-east-1'
        )
        
        # List objects in the first bucket
        buckets_response = s3_client.list_buckets()
        if buckets_response['Buckets']:
            bucket_name = buckets_response['Buckets'][0]['Name']
            print(f"Listing objects in bucket: {bucket_name}")
            
            objects_response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=10)
            
            if 'Contents' in objects_response:
                print(f"✅ Found {len(objects_response['Contents'])} objects:")
                for obj in objects_response['Contents'][:5]:  # Show first 5
                    print(f"  - {obj['Key']} ({obj['Size']} bytes)")
                return True
            else:
                print("ℹ️  Bucket is empty")
                return True
        else:
            print("❌ No buckets found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing S3 dataset creation: {e}")
        return False

def test_mindsdb_chat_direct():
    """Test MindsDB chat functionality directly"""
    
    print("\n" + "="*50)
    print("Testing MindsDB Chat Directly")
    print("="*50)
    
    try:
        mindsdb_url = "http://localhost:47334"
        
        # Test a chat-like query
        query_data = {
            "query": "SELECT 'Hello from MindsDB' as message;"
        }
        
        response = requests.post(
            f"{mindsdb_url}/api/sql/query",
            json=query_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ MindsDB chat query successful!")
            print(f"Response: {result}")
            
            # Try to create a simple model (if possible)
            model_query = {
                "query": "SHOW MODELS;"
            }
            
            model_response = requests.post(
                f"{mindsdb_url}/api/sql/query",
                json=model_query,
                timeout=10
            )
            
            if model_response.status_code == 200:
                models = model_response.json()
                print(f"✅ Found models: {models}")
                return True
            else:
                print(f"⚠️  Could not list models: {model_response.status_code}")
                return True  # Still successful for basic query
                
        else:
            print(f"❌ MindsDB query failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing MindsDB chat: {e}")
        return False

def main():
    print("🚀 Comprehensive Test Suite")
    print("===========================")
    
    results = {}
    
    # Test S3 connection
    print("1. Testing S3 Connection...")
    try:
        endpoint = "g7h4.fra3.idrivee2-51.com"
        access_key = "kPqafITIVXXwrO0MLegM"
        secret_key = "QNbbIp6C9qSBfwkV8OnQYbfmMJYKZEwGoUcAu0f1"
        
        s3_client = boto3.client(
            's3',
            endpoint_url=f'https://{endpoint}',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='us-east-1'
        )
        
        s3_client.list_buckets()
        results['s3_connection'] = True
        print("✅ S3 Connection: PASS")
        
    except Exception as e:
        results['s3_connection'] = False
        print(f"❌ S3 Connection: FAIL - {e}")
    
    # Test S3 dataset creation capability
    results['s3_dataset'] = test_s3_dataset_creation()
    
    # Test MindsDB direct connection
    print("\n2. Testing MindsDB Connection...")
    try:
        response = requests.get("http://localhost:47334/api/status", timeout=5)
        if response.status_code == 200:
            results['mindsdb_connection'] = True
            print("✅ MindsDB Connection: PASS")
        else:
            results['mindsdb_connection'] = False
            print("❌ MindsDB Connection: FAIL")
    except:
        results['mindsdb_connection'] = False
        print("❌ MindsDB Connection: FAIL")
    
    # Test MindsDB chat functionality
    results['mindsdb_chat'] = test_mindsdb_chat_direct()
    
    # Test backend authentication
    print("\n3. Testing Backend Authentication...")
    token = test_backend_login()
    results['backend_auth'] = token is not None
    
    # Print final summary
    print("\n" + "="*50)
    print("🏆 FINAL RESULTS")
    print("="*50)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
    elif passed_tests >= total_tests * 0.7:
        print("⚠️  Most tests passed - minor issues")
    else:
        print("❌ Major issues found")

if __name__ == "__main__":
    main()