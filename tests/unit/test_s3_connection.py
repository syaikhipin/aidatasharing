#!/usr/bin/env python3
"""
Test S3 connection with provided credentials
"""
import requests
import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def test_s3_connection():
    """Test S3 connection with provided credentials"""
    
    # Provided credentials
    endpoint = "g7h4.fra3.idrivee2-51.com"
    access_key = "kPqafITIVXXwrO0MLegM"
    secret_key = "QNbbIp6C9qSBfwkV8OnQYbfmMJYKZEwGoUcAu0f1"
    
    print("Testing S3 Connection...")
    print(f"Endpoint: {endpoint}")
    print(f"Access Key: {access_key}")
    print(f"Secret Key: {secret_key[:8]}...")
    
    try:
        # Create S3 client with custom endpoint
        s3_client = boto3.client(
            's3',
            endpoint_url=f'https://{endpoint}',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='us-east-1'  # Default region
        )
        
        # Test connection by listing buckets
        print("\nTesting connection by listing buckets...")
        response = s3_client.list_buckets()
        
        print("✅ Connection successful!")
        print(f"Found {len(response['Buckets'])} buckets:")
        
        for bucket in response['Buckets']:
            print(f"  - {bucket['Name']} (created: {bucket['CreationDate']})")
            
        return True
        
    except ClientError as e:
        print(f"❌ ClientError: {e}")
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error Code: {error_code}")
        print(f"Error Message: {error_message}")
        return False
        
    except NoCredentialsError:
        print("❌ No credentials found")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_s3_via_backend():
    """Test S3 connection via backend API"""
    
    print("\n" + "="*50)
    print("Testing S3 Connection via Backend API")
    print("="*50)
    
    # Test connection via backend API
    backend_url = "http://localhost:8000"
    
    # First, login to get auth token
    login_data = {
        "username": "alice@techcorp.com",
        "password": "Password123!"
    }
    
    try:
        print("Logging in...")
        login_response = requests.post(f"{backend_url}/api/auth/login", json=login_data)
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Login successful!")
            
            # Create S3 connection
            connection_data = {
                "name": "Test S3 Connection",
                "connection_type": "s3",
                "connection_url": f"s3://{access_key}:{secret_key}@{endpoint}",
                "description": "Test S3 connection using iDrive e2 credentials"
            }
            
            print("Creating S3 connection...")
            conn_response = requests.post(
                f"{backend_url}/api/connectors/",
                json=connection_data,
                headers=headers
            )
            
            if conn_response.status_code in [200, 201]:
                print("✅ Connection created successfully!")
                connection_id = conn_response.json().get("id")
                
                # Test the connection
                print("Testing connection...")
                test_response = requests.post(
                    f"{backend_url}/api/connectors/{connection_id}/test",
                    headers=headers
                )
                
                if test_response.status_code == 200:
                    print("✅ Connection test successful!")
                    return True
                else:
                    print(f"❌ Connection test failed: {test_response.status_code}")
                    print(test_response.text)
                    return False
                    
            else:
                print(f"❌ Failed to create connection: {conn_response.status_code}")
                print(conn_response.text)
                return False
                
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(login_response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error testing via backend: {e}")
        return False

if __name__ == "__main__":
    print("S3 Connection Test")
    print("==================")
    
    # Test direct S3 connection
    direct_result = test_s3_connection()
    
    # Test via backend API
    backend_result = test_s3_via_backend()
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Direct S3 Connection: {'✅ PASS' if direct_result else '❌ FAIL'}")
    print(f"Backend API Test: {'✅ PASS' if backend_result else '❌ FAIL'}")