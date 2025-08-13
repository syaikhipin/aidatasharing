#!/usr/bin/env python3
"""
Focused test to diagnose and fix the MindsDB model access issue.
This script specifically addresses the "Table 'gemini_chat_assistant' not found" error.
"""

import os
import sys
import logging
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

def diagnose_mindsdb_models():
    """Diagnose MindsDB model creation and access issues."""
    logger.info("🔍 Diagnosing MindsDB model access issues...")
    
    try:
        # Ensure connection
        if not mindsdb_service._ensure_connection():
            logger.error("❌ Cannot connect to MindsDB")
            return False
        
        # Check existing models
        logger.info("📋 Checking existing models...")
        try:
            result = mindsdb_service.connection.query("SHOW MODELS")
            if result and hasattr(result, 'fetch'):
                df = result.fetch()
                if not df.empty:
                    models = df.to_dict('records')
                    logger.info(f"Found {len(models)} existing models:")
                    for model in models:
                        logger.info(f"  - {model.get('NAME', 'Unknown')}: {model.get('STATUS', 'Unknown')}")
                else:
                    logger.info("No models found in MindsDB")
            else:
                logger.warning("Could not query models")
        except Exception as e:
            logger.error(f"Error checking models: {e}")
        
        # Check existing engines
        logger.info("🔧 Checking existing engines...")
        try:
            result = mindsdb_service.connection.query("SHOW ML_ENGINES")
            if result and hasattr(result, 'fetch'):
                df = result.fetch()
                if not df.empty:
                    engines = df.to_dict('records')
                    logger.info(f"Found {len(engines)} existing engines:")
                    for engine in engines:
                        logger.info(f"  - {engine.get('NAME', 'Unknown')}: {engine.get('HANDLER', 'Unknown')}")
                else:
                    logger.info("No engines found in MindsDB")
            else:
                logger.warning("Could not query engines")
        except Exception as e:
            logger.error(f"Error checking engines: {e}")
        
        # Check databases
        logger.info("🗄️ Checking existing databases...")
        try:
            result = mindsdb_service.connection.query("SHOW DATABASES")
            if result and hasattr(result, 'fetch'):
                df = result.fetch()
                if not df.empty:
                    databases = df.to_dict('records')
                    logger.info(f"Found {len(databases)} existing databases:")
                    for db in databases:
                        logger.info(f"  - {db.get('Database', 'Unknown')}: {db.get('TYPE', 'Unknown')}")
                else:
                    logger.info("No databases found in MindsDB")
            else:
                logger.warning("Could not query databases")
        except Exception as e:
            logger.error(f"Error checking databases: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Diagnosis failed: {e}")
        return False

def fix_model_access_issue():
    """Try to fix the model access issue by recreating models properly."""
    logger.info("🔧 Attempting to fix model access issue...")
    
    try:
        # Drop existing problematic models
        logger.info("🗑️ Cleaning up existing models...")
        models_to_drop = ["gemini_chat_assistant", "test_chat_model"]
        
        for model_name in models_to_drop:
            try:
                drop_sql = f"DROP MODEL IF EXISTS {model_name}"
                logger.info(f"Dropping model: {model_name}")
                mindsdb_service.connection.query(drop_sql)
                logger.info(f"✅ Model {model_name} dropped")
            except Exception as e:
                logger.warning(f"⚠️ Could not drop model {model_name}: {e}")
        
        # Create engine with proper error handling
        logger.info("🔧 Creating engine...")
        engine_result = mindsdb_service.create_gemini_engine()
        logger.info(f"Engine creation result: {engine_result}")
        
        # Wait a bit for engine to be ready
        import time
        time.sleep(3)
        
        # Create model with explicit table creation
        logger.info("🤖 Creating model with explicit approach...")
        model_name = "gemini_chat_assistant_fixed"
        
        # Use a more explicit model creation approach
        create_model_sql = f"""
        CREATE MODEL {model_name}
        PREDICT response
        USING
            engine = 'google_gemini_engine',
            model_name = 'gemini-2.0-flash',
            prompt_template = 'Answer the following question: {{{{question}}}}',
            max_tokens = 1000;
        """
        
        logger.info(f"Creating model with SQL: {create_model_sql}")
        try:
            result = mindsdb_service.connection.query(create_model_sql)
            logger.info("✅ Model creation command executed")
            
            # Wait for model to initialize
            time.sleep(10)
            
            # Check if model is accessible
            logger.info("🧪 Testing model accessibility...")
            test_query = f"""
            SELECT response 
            FROM {model_name} 
            WHERE question = 'Hello, this is a test'
            """
            
            logger.info(f"Testing with query: {test_query}")
            test_result = mindsdb_service.connection.query(test_query)
            
            if test_result and hasattr(test_result, 'fetch'):
                df = test_result.fetch()
                if not df.empty:
                    logger.info("✅ Model is accessible and working!")
                    response = df.iloc[0]['response'] if 'response' in df.columns else str(df.iloc[0])
                    logger.info(f"Test response: {response}")
                    return True
                else:
                    logger.warning("⚠️ Model query returned empty result")
            else:
                logger.warning("⚠️ Model query failed")
                
        except Exception as model_error:
            logger.error(f"❌ Model creation/testing failed: {model_error}")
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Fix attempt failed: {e}")
        return False

def test_alternative_approach():
    """Test alternative approach using direct MindsDB API."""
    logger.info("🔄 Testing alternative approach...")
    
    try:
        # Try using a simpler model creation approach
        logger.info("🤖 Creating simple test model...")
        
        simple_model_sql = """
        CREATE MODEL simple_test_model
        PREDICT answer
        USING
            engine = 'google_gemini_engine',
            model_name = 'gemini-2.0-flash',
            prompt_template = 'Question: {{question}} Answer:';
        """
        
        try:
            result = mindsdb_service.connection.query(simple_model_sql)
            logger.info("✅ Simple model creation executed")
            
            import time
            time.sleep(8)
            
            # Test the simple model
            test_query = """
            SELECT answer 
            FROM simple_test_model 
            WHERE question = 'What is 2+2?'
            """
            
            logger.info("🧪 Testing simple model...")
            test_result = mindsdb_service.connection.query(test_query)
            
            if test_result and hasattr(test_result, 'fetch'):
                df = test_result.fetch()
                if not df.empty:
                    logger.info("✅ Simple model works!")
                    answer = df.iloc[0]['answer'] if 'answer' in df.columns else str(df.iloc[0])
                    logger.info(f"Answer: {answer}")
                    return True
                else:
                    logger.warning("⚠️ Simple model returned empty result")
            else:
                logger.warning("⚠️ Simple model query failed")
                
        except Exception as e:
            logger.error(f"❌ Simple model test failed: {e}")
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Alternative approach failed: {e}")
        return False

def main():
    """Main function to diagnose and fix MindsDB model issues."""
    logger.info("🚀 Starting MindsDB model access diagnosis and fix...")
    
    # Step 1: Diagnose current state
    if not diagnose_mindsdb_models():
        logger.error("❌ Diagnosis failed, cannot proceed")
        return
    
    # Step 2: Try to fix the issue
    logger.info("🔧 Attempting to fix model access issue...")
    if fix_model_access_issue():
        logger.info("🎉 Model access issue fixed!")
        return
    
    # Step 3: Try alternative approach
    logger.info("🔄 Trying alternative approach...")
    if test_alternative_approach():
        logger.info("🎉 Alternative approach successful!")
        return
    
    logger.error("❌ Could not resolve model access issue")
    logger.info("💡 Recommendations:")
    logger.info("  1. Check MindsDB server logs for detailed error messages")
    logger.info("  2. Verify Google API key is valid and has proper permissions")
    logger.info("  3. Try restarting MindsDB server")
    logger.info("  4. Check if MindsDB version supports the google_gemini engine")

if __name__ == "__main__":
    main()