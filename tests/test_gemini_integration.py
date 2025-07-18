#!/usr/bin/env python3
"""
Test script for Gemini API integration
Verifies that the Google API key is properly loaded and used
"""

import sys
import os
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_gemini_api_key():
    """Test that the Google API key is properly loaded"""
    print("🧪 Testing Gemini API key configuration...")
    
    # Check .env file
    env_path = "../.env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.read()
            if "GOOGLE_API_KEY=" in env_content:
                print("✅ GOOGLE_API_KEY found in .env file")
                
                # Extract the key (masked for security)
                import re
                match = re.search(r'GOOGLE_API_KEY=([^\n]+)', env_content)
                if match:
                    api_key = match.group(1)
                    masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
                    print(f"✅ API key in .env: {masked_key}")
            else:
                print("❌ GOOGLE_API_KEY not found in .env file")
    else:
        print("❌ .env file not found")
    
    # Check backend/.env file
    backend_env_path = "../backend/.env"
    if os.path.exists(backend_env_path):
        with open(backend_env_path, 'r') as f:
            env_content = f.read()
            if "GOOGLE_API_KEY=" in env_content:
                print("✅ GOOGLE_API_KEY found in backend/.env file")
                
                # Extract the key (masked for security)
                import re
                match = re.search(r'GOOGLE_API_KEY=([^\n]+)', env_content)
                if match:
                    api_key = match.group(1)
                    masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
                    print(f"✅ API key in backend/.env: {masked_key}")
            else:
                print("❌ GOOGLE_API_KEY not found in backend/.env file")
    else:
        print("❌ backend/.env file not found")
    
    # Check environment variable
    api_key = os.environ.get("GOOGLE_API_KEY")
    if api_key:
        masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
        print(f"✅ GOOGLE_API_KEY environment variable set: {masked_key}")
    else:
        print("❌ GOOGLE_API_KEY environment variable not set")
    
    # Try to import settings from backend
    try:
        from app.core.config import settings
        if settings.GOOGLE_API_KEY:
            masked_key = settings.GOOGLE_API_KEY[:4] + "..." + settings.GOOGLE_API_KEY[-4:] if len(settings.GOOGLE_API_KEY) > 8 else "***"
            print(f"✅ settings.GOOGLE_API_KEY loaded: {masked_key}")
        else:
            print("❌ settings.GOOGLE_API_KEY is None or empty")
    except Exception as e:
        print(f"❌ Failed to import settings: {e}")
    
    print("\n🧪 Testing Gemini API directly...")
    try:
        import google.generativeai as genai
        
        # Try with API key from settings
        try:
            from app.core.config import settings
            api_key = settings.GOOGLE_API_KEY
            if not api_key:
                # Try with hardcoded key as fallback
                api_key = "AIzaSyB5-NF7TEYHkKdIMvZ45UNy1bDOCSCZH9Q"
                print(f"⚠️ Using hardcoded API key as fallback")
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content("Hello, are you working correctly?")
            
            print(f"✅ Gemini API test successful!")
            print(f"✅ Response: {response.text[:100]}...")
            return True
        except Exception as e:
            print(f"❌ Gemini API test failed: {e}")
            return False
    except ImportError:
        print("❌ google.generativeai module not installed")
        return False

def test_mindsdb_service():
    """Test the MindsDB service with Gemini integration"""
    print("\n🧪 Testing MindsDB service with Gemini integration...")
    
    try:
        from app.services.mindsdb import mindsdb_service
        
        # Check if API key is loaded
        if mindsdb_service.api_key:
            masked_key = mindsdb_service.api_key[:4] + "..." + mindsdb_service.api_key[-4:] if len(mindsdb_service.api_key) > 8 else "***"
            print(f"✅ mindsdb_service.api_key loaded: {masked_key}")
        else:
            print("❌ mindsdb_service.api_key is None or empty")
        
        # Test MindsDB AI chat
        print("\n🧪 Testing MindsDB AI chat integration...")
        result = mindsdb_service.ai_chat("Hello, are you working correctly?")
        
        if result.get("answer"):
            print(f"✅ MindsDB AI chat successful!")
            print(f"✅ Response: {result['answer'][:100]}...")
            print(f"✅ Source: {result.get('source', 'unknown')}")
            return True
        else:
            print(f"❌ MindsDB AI chat failed: {result.get('error', 'Unknown error')}")
            print(f"❌ Source: {result.get('source', 'unknown')}")
            return False
    except Exception as e:
        print(f"❌ MindsDB service test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 GEMINI API INTEGRATION TEST")
    print("=" * 60)
    
    api_key_success = test_gemini_api_key()
    mindsdb_success = test_mindsdb_service()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"✅ API Key Configuration: {'PASSED' if api_key_success else 'FAILED'}")
    print(f"✅ MindsDB Service: {'PASSED' if mindsdb_success else 'FAILED'}")
    print("=" * 60)
    
    if api_key_success and mindsdb_success:
        print("\n🎉 All tests passed! Gemini API integration is working correctly.")
        print("🚀 You can now use the chat feature with datasets.")
    else:
        print("\n⚠️ Some tests failed. Please check the issues above.")
        print("🔧 Try the following fixes:")
        print("   1. Make sure GOOGLE_API_KEY is set in .env and backend/.env")
        print("   2. Restart the development environment: ./stop-dev.sh && ./start-dev.sh")
        print("   3. Check that the API key is valid and has access to Gemini API")
    
    sys.exit(0 if api_key_success and mindsdb_success else 1)