#!/usr/bin/env python3
"""
Advanced MindsDB AI Chat Model Diagnostic and Fix Script
This script performs deep analysis of MindsDB model issues and implements multiple fix strategies.
"""

import os
import sys
import logging
import time
from datetime import datetime

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_app_dir = os.path.join(backend_dir, 'backend')
sys.path.insert(0, backend_app_dir)

from app.services.mindsdb import mindsdb_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_google_api_key():
    """Check if Google API key is properly configured."""
    logger.info("🔑 Checking Google API key configuration...")
    
    try:
        # Check environment variables
        import os
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
            masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
            logger.info(f"✅ Google API key found in environment: {masked_key}")
        else:
            logger.warning("⚠️ No Google API key found in environment")
        
        # Check MindsDB service configuration
        if mindsdb_service.api_key:
            masked_key = mindsdb_service.api_key[:4] + "..." + mindsdb_service.api_key[-4:] if len(mindsdb_service.api_key) > 8 else "***"
            logger.info(f"✅ Google API key loaded in MindsDB service: {masked_key}")
            return True
        else:
            logger.error("❌ No Google API key in MindsDB service")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error checking Google API key: {e}")
        return False

def test_direct_google_api():
    """Test Google Gemini API directly without MindsDB."""
    logger.info("🧪 Testing direct Google Gemini API access...")
    
    try:
        import google.generativeai as genai
        
        # Configure with the API key
        genai.configure(api_key=mindsdb_service.api_key)
        
        # List available models
        logger.info("📋 Available Gemini models:")
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                logger.info(f"  - {model.name}")
        
        # Test a simple generation
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Hello, this is a test. Please respond with 'API working correctly'.")
        
        logger.info(f"✅ Direct API test successful: {response.text}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Direct API test failed: {e}")
        return False

def check_mindsdb_handlers():
    """Check available handlers in MindsDB."""
    logger.info("🔧 Checking available MindsDB handlers...")
    
    try:
        if not mindsdb_service._ensure_connection():
            logger.error("❌ Cannot connect to MindsDB")
            return False
        
        # Check available handlers
        result = mindsdb_service.connection.query("SHOW HANDLERS")
        if result and hasattr(result, 'fetch'):
            df = result.fetch()
            if not df.empty:
                handlers = df.to_dict('records')
                logger.info(f"Found {len(handlers)} available handlers:")
                
                google_handlers = [h for h in handlers if 'google' in h.get('name', '').lower() or 'gemini' in h.get('name', '').lower()]
                if google_handlers:
                    logger.info("🎯 Google/Gemini related handlers:")
                    for handler in google_handlers:
                        logger.info(f"  - {handler.get('name', 'Unknown')}: {handler.get('title', 'No title')}")
                    return True
                else:
                    logger.warning("⚠️ No Google/Gemini handlers found")
                    return False
            else:
                logger.warning("⚠️ No handlers found")
                return False
        else:
            logger.error("❌ Could not query handlers")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error checking handlers: {e}")
        return False

def try_openai_engine():
    """Try creating and testing an OpenAI engine as alternative."""
    logger.info("🔄 Trying OpenAI engine as alternative...")
    
    try:
        # Check for OpenAI API key
        import os
        openai_key = os.environ.get('OPENAI_API_KEY')
        if not openai_key:
            logger.warning("⚠️ No OpenAI API key found, skipping OpenAI test")
            return False
        
        # Create OpenAI engine
        engine_name = "openai_test_engine"
        create_engine_sql = f"""
        CREATE ML_ENGINE {engine_name}
        FROM openai
        USING
            api_key = '{openai_key}';
        """
        
        logger.info(f"🔧 Creating OpenAI engine: {engine_name}")
        mindsdb_service.connection.query(create_engine_sql)
        
        time.sleep(2)
        
        # Create OpenAI model
        model_name = "openai_test_model"
        create_model_sql = f"""
        CREATE MODEL {model_name}
        PREDICT response
        USING
            engine = '{engine_name}',
            model_name = 'gpt-3.5-turbo',
            prompt_template = 'Answer the following question: {{{{question}}}}';
        """
        
        logger.info(f"🤖 Creating OpenAI model: {model_name}")
        mindsdb_service.connection.query(create_model_sql)
        
        time.sleep(5)
        
        # Test the OpenAI model
        test_query = f"""
        SELECT response 
        FROM {model_name} 
        WHERE question = 'What is 2+2? Answer with just the number.'
        """
        
        logger.info("🧪 Testing OpenAI model...")
        result = mindsdb_service.connection.query(test_query)
        
        if result and hasattr(result, 'fetch'):
            df = result.fetch()
            if not df.empty:
                response = df.iloc[0]['response'] if 'response' in df.columns else str(df.iloc[0])
                logger.info(f"✅ OpenAI model works! Response: {response}")
                return True
            else:
                logger.warning("⚠️ OpenAI model returned empty result")
        else:
            logger.warning("⚠️ OpenAI model query failed")
        
        return False
        
    except Exception as e:
        logger.error(f"❌ OpenAI engine test failed: {e}")
        return False

def try_alternative_gemini_setup():
    """Try alternative Gemini engine setup approaches."""
    logger.info("🔄 Trying alternative Gemini engine setup...")
    
    try:
        # Method 1: Try with different engine parameters
        logger.info("📝 Method 1: Alternative Gemini engine parameters")
        
        engine_name = "gemini_alt_engine"
        create_engine_sql = f"""
        CREATE ML_ENGINE {engine_name}
        FROM google_gemini
        USING
            api_key = '{mindsdb_service.api_key}',
            model = 'gemini-2.0-flash';
        """
        
        logger.info(f"🔧 Creating alternative Gemini engine: {engine_name}")
        mindsdb_service.connection.query(create_engine_sql)
        
        time.sleep(3)
        
        # Create model with alternative approach
        model_name = "gemini_alt_model"
        create_model_sql = f"""
        CREATE MODEL {model_name}
        PREDICT answer
        USING
            engine = '{engine_name}',
            prompt_template = 'Question: {{{{question}}}} Answer:';
        """
        
        logger.info(f"🤖 Creating alternative Gemini model: {model_name}")
        mindsdb_service.connection.query(create_model_sql)
        
        time.sleep(8)
        
        # Test the alternative model
        test_query = f"""
        SELECT answer 
        FROM {model_name} 
        WHERE question = 'Hello, please respond with TEST SUCCESSFUL'
        """
        
        logger.info("🧪 Testing alternative Gemini model...")
        result = mindsdb_service.connection.query(test_query)
        
        if result and hasattr(result, 'fetch'):
            df = result.fetch()
            if not df.empty:
                answer = df.iloc[0]['answer'] if 'answer' in df.columns else str(df.iloc[0])
                logger.info(f"✅ Alternative Gemini model works! Answer: {answer}")
                return True
            else:
                logger.warning("⚠️ Alternative Gemini model returned empty result")
        else:
            logger.warning("⚠️ Alternative Gemini model query failed")
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Alternative Gemini setup failed: {e}")
        return False

def fix_mindsdb_service():
    """Update MindsDB service to use working engine."""
    logger.info("🔧 Updating MindsDB service configuration...")
    
    try:
        # Check which engines are working
        working_engines = []
        
        # Test OpenAI
        try:
            test_query = "SELECT response FROM openai_test_model WHERE question = 'test' LIMIT 1"
            result = mindsdb_service.connection.query(test_query)
            if result and hasattr(result, 'fetch'):
                df = result.fetch()
                if not df.empty:
                    working_engines.append(("openai_test_engine", "openai_test_model"))
        except:
            pass
        
        # Test alternative Gemini
        try:
            test_query = "SELECT answer FROM gemini_alt_model WHERE question = 'test' LIMIT 1"
            result = mindsdb_service.connection.query(test_query)
            if result and hasattr(result, 'fetch'):
                df = result.fetch()
                if not df.empty:
                    working_engines.append(("gemini_alt_engine", "gemini_alt_model"))
        except:
            pass
        
        if working_engines:
            engine_name, model_name = working_engines[0]
            logger.info(f"✅ Found working engine: {engine_name} with model: {model_name}")
            
            # Update the MindsDB service configuration
            mindsdb_service.engine_name = engine_name
            mindsdb_service.chat_model_name = model_name
            
            logger.info(f"🔧 Updated MindsDB service to use {engine_name}")
            return True
        else:
            logger.error("❌ No working engines found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error updating MindsDB service: {e}")
        return False

def test_final_chat():
    """Test the final chat functionality."""
    logger.info("🎯 Testing final chat functionality...")
    
    try:
        result = mindsdb_service.ai_chat("Hello, please respond with 'CHAT SYSTEM WORKING'")
        
        if result and result.get("answer"):
            logger.info(f"✅ Chat system working! Response: {result.get('answer')}")
            return True
        else:
            logger.error(f"❌ Chat system failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Final chat test failed: {e}")
        return False

def main():
    """Main diagnostic and fix function."""
    logger.info("🚀 Starting advanced MindsDB AI chat model diagnostic and fix...")
    
    steps = [
        ("Check Google API Key", check_google_api_key),
        ("Test Direct Google API", test_direct_google_api),
        ("Check MindsDB Handlers", check_mindsdb_handlers),
        ("Try OpenAI Engine", try_openai_engine),
        ("Try Alternative Gemini Setup", try_alternative_gemini_setup),
        ("Fix MindsDB Service", fix_mindsdb_service),
        ("Test Final Chat", test_final_chat),
    ]
    
    results = {}
    
    for step_name, step_func in steps:
        logger.info(f"🔄 Step: {step_name}")
        try:
            results[step_name] = step_func()
            status = "✅ PASS" if results[step_name] else "❌ FAIL"
            logger.info(f"   Result: {status}")
        except Exception as e:
            logger.error(f"   Error: {e}")
            results[step_name] = False
        
        logger.info("")  # Empty line for readability
    
    # Summary
    logger.info("📋 Final Results Summary:")
    for step_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  - {step_name}: {status}")
    
    passed_steps = sum(results.values())
    total_steps = len(results)
    
    logger.info(f"🎯 Overall Result: {passed_steps}/{total_steps} steps passed")
    
    if results.get("Test Final Chat", False):
        logger.info("🎉 SUCCESS: AI chat models are now working!")
    elif any([results.get("Try OpenAI Engine", False), results.get("Try Alternative Gemini Setup", False)]):
        logger.info("⚠️ PARTIAL SUCCESS: Alternative engines working, manual configuration needed")
    else:
        logger.error("❌ FAILURE: Could not get AI chat models working")
    
    return results

if __name__ == "__main__":
    main()