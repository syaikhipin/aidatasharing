#!/usr/bin/env python3
"""
Fix MindsDB model creation and test model functionality.
"""

import sys
import os
import time
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.mindsdb import MindsDBService
from app.core.config import settings

def fix_mindsdb_models():
    """Fix MindsDB model creation and test functionality."""
    print("🔧 Fixing MindsDB Models")
    print("=" * 40)
    
    # Initialize MindsDB service
    mindsdb_service = MindsDBService()
    
    if not mindsdb_service._ensure_connection():
        print("❌ Cannot connect to MindsDB")
        return
    
    print("✅ Connected to MindsDB")
    
    # First, let's check what engines are actually available
    print("\n🔍 Checking available engines...")
    try:
        engines_query = "SHOW ML_ENGINES"
        result = mindsdb_service.connection.query(engines_query)
        engines_df = result.fetch()
        
        print(f"Available engines:")
        if not engines_df.empty:
            for _, engine in engines_df.iterrows():
                engine_name = engine.get('NAME', 'Unknown')
                engine_handler = engine.get('HANDLER', 'Unknown')
                print(f"  - {engine_name} ({engine_handler})")
        else:
            print("  No engines found")
            
    except Exception as e:
        print(f"❌ Error checking engines: {e}")
    
    # Try to create the engine with proper error handling
    print(f"\n🔧 Creating Gemini engine...")
    try:
        # Use the correct engine creation syntax
        create_engine_sql = f"""
        CREATE ML_ENGINE IF NOT EXISTS {settings.GEMINI_ENGINE_NAME}
        FROM google_gemini
        USING
            api_key = '{settings.GOOGLE_API_KEY}';
        """
        
        print(f"SQL: {create_engine_sql}")
        result = mindsdb_service.connection.query(create_engine_sql)
        print("✅ Engine creation query executed")
        
        # Wait a moment
        time.sleep(2)
        
        # Check engines again
        result = mindsdb_service.connection.query("SHOW ML_ENGINES")
        engines_df = result.fetch()
        
        gemini_engine_exists = False
        if not engines_df.empty:
            for _, engine in engines_df.iterrows():
                if engine.get('NAME') == settings.GEMINI_ENGINE_NAME:
                    gemini_engine_exists = True
                    print(f"✅ Gemini engine found: {engine.get('NAME')}")
                    break
        
        if not gemini_engine_exists:
            print("❌ Gemini engine not found after creation")
            return
            
    except Exception as e:
        print(f"❌ Engine creation failed: {e}")
        return
    
    # Now try to create the model with proper syntax
    print(f"\n🤖 Creating chat model...")
    try:
        model_name = settings.GEMINI_CHAT_MODEL_NAME
        
        # Use the correct model creation syntax for Gemini
        create_model_sql = f"""
        CREATE MODEL IF NOT EXISTS {model_name}
        PREDICT response
        USING
            engine = '{settings.GEMINI_ENGINE_NAME}',
            model = '{settings.DEFAULT_GEMINI_MODEL}',
            question_column = 'question';
        """
        
        print(f"SQL: {create_model_sql}")
        result = mindsdb_service.connection.query(create_model_sql)
        print("✅ Model creation query executed")
        
        # Wait for model to initialize
        print("⏳ Waiting for model to initialize...")
        time.sleep(5)
        
        # Check if model exists
        models_query = "SHOW MODELS"
        result = mindsdb_service.connection.query(models_query)
        models_df = result.fetch()
        
        model_found = False
        if not models_df.empty:
            for _, model in models_df.iterrows():
                if model.get('NAME') == model_name:
                    model_found = True
                    model_status = model.get('STATUS', 'Unknown')
                    print(f"✅ Model found: {model_name} (Status: {model_status})")
                    break
        
        if not model_found:
            print(f"❌ Model {model_name} not found after creation")
            return
            
    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        return
    
    # Test the model with a simple query
    print(f"\n💬 Testing model with simple query...")
    try:
        test_question = "Hello, can you respond with a simple greeting?"
        
        # Try different query formats
        query_formats = [
            f"SELECT response FROM {model_name} WHERE question = '{test_question}'",
            f"SELECT * FROM {model_name} WHERE question = '{test_question}'",
        ]
        
        for i, query in enumerate(query_formats, 1):
            print(f"\n🔍 Test {i}: {query}")
            try:
                result = mindsdb_service.connection.query(query)
                print(f"   Query executed successfully")
                
                df = result.fetch()
                print(f"   Result type: {type(df)}")
                print(f"   Result shape: {df.shape if hasattr(df, 'shape') else 'N/A'}")
                
                if not df.empty:
                    print(f"   ✅ Got response!")
                    print(f"   Columns: {list(df.columns)}")
                    print(f"   First row: {df.iloc[0].to_dict()}")
                    
                    # Try to extract the response
                    if 'response' in df.columns:
                        response = df.iloc[0]['response']
                        print(f"   Response: {response}")
                    else:
                        print(f"   Available columns: {list(df.columns)}")
                        print(f"   Full row data: {df.iloc[0]}")
                else:
                    print(f"   ❌ Empty result")
                    
            except Exception as e:
                print(f"   ❌ Query failed: {e}")
    
    except Exception as e:
        print(f"❌ Model testing failed: {e}")
    
    # Final status check
    print(f"\n📊 Final Status Check...")
    try:
        # Check model status
        status_query = f"DESCRIBE {model_name}"
        result = mindsdb_service.connection.query(status_query)
        df = result.fetch()
        
        if not df.empty:
            print(f"Model description:")
            for _, row in df.iterrows():
                print(f"  {row.to_dict()}")
        else:
            print("No model description available")
            
    except Exception as e:
        print(f"❌ Status check failed: {e}")
    
    print(f"\n" + "=" * 40)
    print("🔧 Model Fix Complete")

def main():
    """Main function."""
    fix_mindsdb_models()

if __name__ == "__main__":
    main()