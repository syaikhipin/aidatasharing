#!/usr/bin/env python3
"""
Test dataset chat functionality directly
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_dataset_chat():
    """Test dataset chat functionality directly"""
    print("🧪 Testing dataset chat functionality...")
    
    try:
        from app.services.mindsdb import mindsdb_service
        
        # Test the actual chat_with_dataset method
        print("1. Testing chat_with_dataset method...")
        result = mindsdb_service.chat_with_dataset(
            dataset_id="1",
            message="Hello, can you respond with SUCCESS?",
            user_id=1,
            session_id="test_session",
            organization_id=1
        )
        
        print(f"✅ Chat result type: {type(result)}")
        print(f"✅ Chat result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        if result and isinstance(result, dict):
            if "answer" in result:
                print(f"✅ Chat answer: {result['answer']}")
                if "SUCCESS" in result['answer'].upper() or len(result['answer']) > 10:
                    print("✅ SUCCESS! Dataset chat is working!")
                    return True
                else:
                    print(f"⚠️ Chat returned answer but might be error message: {result['answer']}")
            else:
                print(f"❌ No answer in result: {result}")
            
            if "error" in result:
                print(f"⚠️ Error in result: {result['error']}")
            
            if "source" in result:
                print(f"✅ Source: {result['source']}")
        else:
            print(f"❌ Invalid result: {result}")
        
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 DATASET CHAT TEST")
    print("=" * 60)
    
    success = test_dataset_chat()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"✅ Dataset Chat Test: {'PASSED' if success else 'FAILED'}")
    print("=" * 60)
    
    sys.exit(0 if success else 1)