#!/usr/bin/env python3
"""
Simple CSV Reading Test with Gemini
===================================

This test uploads a CSV file and directly tests if Gemini can read and analyze the content
through the dataset chat endpoint.
"""

import requests
import json
import time

def main():
    base_url = "http://localhost:8000"
    
    print("🧪 Simple CSV-Gemini Integration Test")
    print("=" * 50)
    
    # 1. Authenticate
    print("🔐 Authenticating...")
    auth_response = requests.post(
        f"{base_url}/api/auth/login",
        data={"username": "admin@example.com", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if auth_response.status_code != 200:
        print(f"❌ Authentication failed: {auth_response.status_code}")
        return False
    
    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Authenticated")
    
    # 2. Upload CSV dataset
    print("\n📤 Uploading CSV dataset...")
    
    with open('test_data.csv', 'rb') as f:
        files = {'file': ('test_data.csv', f, 'text/csv')}
        data = {
            'name': 'CSV Test Data',
            'description': 'Test CSV for Gemini integration',
            'sharing_level': 'ORGANIZATION'
        }
        
        upload_response = requests.post(
            f"{base_url}/api/datasets/upload",
            files=files,
            data=data,
            headers=headers
        )
    
    if upload_response.status_code not in [200, 201]:
        print(f"❌ Upload failed: {upload_response.status_code}")
        print(upload_response.text)
        return False
    
    result = upload_response.json()
    dataset_id = result["dataset"]["id"]
    print(f"✅ Dataset uploaded: ID {dataset_id}")
    
    # 3. Wait for processing and check if AI chat is available
    print("\n⏳ Waiting for AI model to be ready...")
    time.sleep(5)
    
    # Check if models are available
    models_response = requests.get(
        f"{base_url}/api/datasets/{dataset_id}/models",
        headers=headers
    )
    
    if models_response.status_code == 200:
        models_info = models_response.json()
        print(f"📊 Models available: {models_info.get('models', [])}")
    
    # 4. Test CSV data chat with specific questions about the CSV content
    test_questions = [
        "What products are in this dataset?",
        "How many rows of data are there?",
        "What is the total revenue from all products?",
        "Which product has the highest sales amount?",
        "List all the categories in the data"
    ]
    
    successful_chats = 0
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🔍 Test {i}: {question}")
        
        chat_response = requests.post(
            f"{base_url}/api/datasets/{dataset_id}/chat",
            json={"message": question},
            headers=headers
        )
        
        if chat_response.status_code == 200:
            result = chat_response.json()
            answer = result.get("response", result.get("answer", "No response"))
            print(f"💬 Gemini: {answer[:200]}...")
            print(f"📝 Full response: {answer}")  # Show full response
            
            # Check if the response contains relevant information about our CSV
            answer_lower = answer.lower()
            relevant_keywords = ['laptop', 'phone', 'tablet', 'headphones', 'electronics', 'audio', '1299', '699', '399']
            
            if any(keyword in answer_lower for keyword in relevant_keywords):
                print("✅ Response contains CSV-specific data!")
                successful_chats += 1
            else:
                print("⚠️  Response doesn't seem to reference CSV data")
        else:
            print(f"❌ Chat failed: {chat_response.status_code}")
            print(chat_response.text)
    
    # 5. Summary
    print("\n" + "=" * 50)
    print("🎯 TEST RESULTS")
    print("=" * 50)
    success_rate = (successful_chats / len(test_questions)) * 100
    print(f"📊 Successful CSV-aware responses: {successful_chats}/{len(test_questions)} ({success_rate:.1f}%)")
    
    if success_rate >= 60:
        print("🎉 SUCCESS: Gemini CAN read and analyze CSV data!")
        print("✅ The integration successfully feeds CSV content to Gemini")
        return True
    else:
        print("❌ FAILURE: Limited CSV data understanding detected")
        print("⚠️  Gemini may not be receiving proper CSV data")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 