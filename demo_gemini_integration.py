#!/usr/bin/env python3
"""
AI Share Platform - Gemini Integration Demo

This script demonstrates the complete Gemini integration with MindsDB SDK
for data chat functionality.
"""

import os
import sys
import json
import asyncio
from datetime import datetime

# Add backend path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

def print_banner():
    """Print demo banner."""
    print("=" * 80)
    print("🚀 AI SHARE PLATFORM - GEMINI INTEGRATION DEMO")
    print("=" * 80)
    print("This demo showcases the MindsDB SDK integration with Gemini AI")
    print("for advanced data chat functionality.")
    print("=" * 80)

def check_environment():
    """Check if environment is properly configured."""
    print("\n🔍 Checking Environment Configuration...")
    
    try:
        from app.core.config import settings
        
        required_vars = {
            'GOOGLE_API_KEY': settings.GOOGLE_API_KEY,
            'MINDSDB_URL': settings.MINDSDB_URL,
            'GEMINI_ENGINE_NAME': settings.GEMINI_ENGINE_NAME,
            'DEFAULT_GEMINI_MODEL': settings.DEFAULT_GEMINI_MODEL
        }
        
        all_configured = True
        for var_name, var_value in required_vars.items():
            if var_value:
                if var_name == 'GOOGLE_API_KEY':
                    masked_value = '*' * (len(str(var_value)) - 8) + str(var_value)[-8:]
                    print(f"  ✅ {var_name}: {masked_value}")
                else:
                    print(f"  ✅ {var_name}: {var_value}")
            else:
                print(f"  ❌ {var_name}: Not configured")
                all_configured = False
        
        return all_configured
        
    except Exception as e:
        print(f"  ❌ Environment check failed: {e}")
        return False

def demo_mindsdb_connection():
    """Demonstrate MindsDB connection."""
    print("\n🧠 Testing MindsDB Connection...")
    
    try:
        from app.services.mindsdb import mindsdb_service
        
        health = mindsdb_service.check_health()
        
        print(f"  Connection Status: {'✅ Connected' if health.get('mindsdb_available') else '⚠️ Fallback Mode'}")
        print(f"  MindsDB URL: {health.get('mindsdb_url')}")
        print(f"  API Key: {'✅ Configured' if health.get('api_key_configured') else '❌ Missing'}")
        
        if health.get('mindsdb_available'):
            print(f"  Engine Count: {health.get('engines_count', 'unknown')}")
            print(f"  Gemini Engine: {'✅ Ready' if health.get('gemini_engine_exists') else '⚠️ Needs Setup'}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Connection test failed: {e}")
        return False

def demo_engine_setup():
    """Demonstrate Gemini engine setup."""
    print("\n🔧 Setting up Gemini Engine...")
    
    try:
        from app.services.mindsdb import mindsdb_service
        
        result = mindsdb_service.create_gemini_engine()
        
        if result.get("status") in ["created", "exists"]:
            print(f"  ✅ {result.get('message')}")
            return True
        else:
            print(f"  ❌ Engine setup failed: {result}")
            return False
            
    except Exception as e:
        print(f"  ❌ Engine setup failed: {e}")
        return False

def demo_chat_model():
    """Demonstrate chat model creation."""
    print("\n🤖 Creating Chat Model...")
    
    try:
        from app.services.mindsdb import mindsdb_service
        
        model_name = "demo_chat_model"
        result = mindsdb_service.create_gemini_model(
            model_name=model_name,
            model_type="chat",
            prompt_template="You are a helpful AI assistant for data analysis. Answer: {{question}}"
        )
        
        if result.get("status") in ["created", "exists"]:
            print(f"  ✅ {result.get('message')}")
            return model_name
        else:
            print(f"  ❌ Model creation failed: {result}")
            return None
            
    except Exception as e:
        print(f"  ❌ Model creation failed: {e}")
        return None

def demo_basic_chat():
    """Demonstrate basic AI chat."""
    print("\n💬 Testing Basic AI Chat...")
    
    try:
        from app.services.mindsdb import mindsdb_service
        
        questions = [
            "What is artificial intelligence?",
            "How can AI help with data analysis?",
            "What are the benefits of using MindsDB?"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n  Question {i}: {question}")
            
            response = mindsdb_service.ai_chat(question)
            
            if response.get("answer"):
                answer = response.get("answer")
                model = response.get("model", "unknown")
                source = response.get("source", "unknown")
                
                print(f"  Answer: {answer[:150]}...")
                print(f"  Model: {model}")
                print(f"  Source: {source}")
            else:
                print(f"  ❌ No response received")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Chat test failed: {e}")
        return False

def demo_dataset_model():
    """Demonstrate dataset-specific model creation."""
    print("\n📊 Creating Dataset-Specific Model...")
    
    try:
        from app.services.mindsdb import mindsdb_service
        
        dataset_id = 42
        dataset_name = "demo_sales_data"
        
        result = mindsdb_service.create_dataset_ml_model(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            dataset_type="CSV"
        )
        
        if result.get("success"):
            print(f"  ✅ {result.get('message')}")
            print(f"  Model Name: {result.get('chat_model')}")
            print(f"  Engine: {result.get('engine')}")
            return dataset_id
        else:
            print(f"  ❌ Dataset model creation failed: {result.get('error')}")
            return None
            
    except Exception as e:
        print(f"  ❌ Dataset model creation failed: {e}")
        return None

def demo_dataset_chat(dataset_id):
    """Demonstrate dataset-specific chat."""
    print(f"\n📈 Testing Dataset Chat (ID: {dataset_id})...")
    
    try:
        from app.services.mindsdb import mindsdb_service
        
        questions = [
            "What insights can you provide about this sales dataset?",
            "What are the key trends in the data?",
            "How can we improve sales performance based on this data?"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n  Question {i}: {question}")
            
            response = mindsdb_service.chat_with_dataset(
                dataset_id=dataset_id,
                message=question
            )
            
            if response.get("answer"):
                answer = response.get("answer")
                model = response.get("model", "unknown")
                source = response.get("source", "unknown")
                
                print(f"  Answer: {answer[:150]}...")
                print(f"  Model: {model}")
                print(f"  Source: {source}")
                
                if response.get("note"):
                    print(f"  Note: {response.get('note')}")
            else:
                print(f"  ❌ No response received")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Dataset chat test failed: {e}")
        return False

def demo_integration_init():
    """Demonstrate complete integration initialization."""
    print("\n🚀 Testing Complete Integration Initialization...")
    
    try:
        from app.services.mindsdb import mindsdb_service
        
        result = mindsdb_service.initialize_gemini_integration()
        
        print(f"  Overall Status: {result.get('overall_status')}")
        
        components = result.get("components", {})
        for component, details in components.items():
            status = details.get("status")
            emoji = "✅" if status == "success" else "❌"
            print(f"  {emoji} {component.replace('_', ' ').title()}: {status}")
            
            if status == "error":
                print(f"    Error: {details.get('error')}")
        
        # Show configuration
        config = result.get("configuration", {})
        print(f"\n  Configuration:")
        print(f"    Engine: {config.get('engine_name')}")
        print(f"    API Key: {'✅ OK' if config.get('api_key_configured') else '❌ Missing'}")
        print(f"    Connection: {config.get('connection_status')}")
        
        return result.get('overall_status') == 'success'
        
    except Exception as e:
        print(f"  ❌ Integration initialization failed: {e}")
        return False

def cleanup_demo_resources():
    """Clean up demo resources."""
    print("\n🧹 Cleaning up demo resources...")
    
    try:
        from app.services.mindsdb import mindsdb_service
        
        # Clean up dataset model
        result = mindsdb_service.delete_dataset_models(42)
        if result.get("success"):
            print("  ✅ Demo dataset models cleaned up")
        else:
            print(f"  ⚠️ Cleanup warning: {result.get('error')}")
        
        print("  ✅ Demo cleanup completed")
        
    except Exception as e:
        print(f"  ⚠️ Cleanup warning: {e}")

def generate_demo_report(results):
    """Generate demo report."""
    print("\n" + "=" * 80)
    print("📊 DEMO RESULTS SUMMARY")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"Total Demos: {total_tests}")
    print(f"Successful: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    print(f"\nDetailed Results:")
    for demo_name, success in results.items():
        emoji = "✅" if success else "❌"
        print(f"  {emoji} {demo_name.replace('_', ' ').title()}")
    
    if success_rate >= 80:
        status = "🎉 EXCELLENT - Ready for production!"
    elif success_rate >= 60:
        status = "👍 GOOD - Minor issues to address"
    else:
        status = "⚠️ NEEDS WORK - Several issues found"
    
    print(f"\nOverall Status: {status}")
    print("=" * 80)
    
    return success_rate >= 80

def main():
    """Main demo function."""
    print_banner()
    
    results = {}
    
    # Environment check
    if not check_environment():
        print("\n❌ Environment not properly configured. Please check your .env file.")
        return False
    
    print("\n🚀 Starting Gemini Integration Demo...")
    
    # Test sequence
    results["environment"] = check_environment()
    results["mindsdb_connection"] = demo_mindsdb_connection()
    results["engine_setup"] = demo_engine_setup()
    results["chat_model"] = demo_chat_model() is not None
    results["basic_chat"] = demo_basic_chat()
    
    # Dataset-specific tests
    dataset_id = demo_dataset_model()
    results["dataset_model"] = dataset_id is not None
    
    if dataset_id:
        results["dataset_chat"] = demo_dataset_chat(dataset_id)
    else:
        results["dataset_chat"] = False
    
    # Integration test
    results["integration_init"] = demo_integration_init()
    
    # Cleanup
    cleanup_demo_resources()
    
    # Generate report
    success = generate_demo_report(results)
    
    if success:
        print("\n🎉 Demo completed successfully! Your Gemini integration is working!")
        print("\n💡 Next steps:")
        print("  1. Upload a real dataset through the frontend")
        print("  2. Create AI models for your data")
        print("  3. Start chatting with your data!")
        print("  4. Explore the analytics dashboard")
    else:
        print("\n⚠️ Some issues were found. Please check the logs above.")
        print("\n🔧 Troubleshooting:")
        print("  1. Ensure MindsDB is running")
        print("  2. Check your Google API key")
        print("  3. Verify network connectivity")
        print("  4. Review the backend logs")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1) 