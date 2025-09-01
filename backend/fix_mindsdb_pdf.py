#!/usr/bin/env python3
"""
Upload PDF to MindsDB files database and create a proper RAG model.
"""

import sys
import os
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.dataset import Dataset
from app.services.mindsdb import MindsDBService

def upload_pdf_to_mindsdb():
    """Upload the PDF file to MindsDB files database."""
    
    # File paths
    storage_base = '/Users/syaikhipin/Documents/program/simpleaisharing/storage'
    file_path = 'org_1/dataset_35_20250831_000228_0a3c45d7a96b3f58.pdf'
    full_path = os.path.join(storage_base, file_path)
    
    if not os.path.exists(full_path):
        print(f"❌ PDF file not found at: {full_path}")
        return False
    
    print(f"✅ Found PDF file: {full_path}")
    
    # Upload to MindsDB via REST API
    mindsdb_url = "http://127.0.0.1:47334"  # Default MindsDB URL
    file_name = "agentic_memory_pdf"  # Simple name for MindsDB
    
    try:
        # Upload file to MindsDB
        with open(full_path, 'rb') as f:
            files = {'file': (file_name + '.pdf', f, 'application/pdf')}
            response = requests.put(
                f"{mindsdb_url}/api/files/{file_name}",
                files=files
            )
        
        if response.status_code == 200:
            print(f"✅ Successfully uploaded PDF to MindsDB as '{file_name}'")
            return file_name
        else:
            print(f"❌ Failed to upload PDF to MindsDB: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error uploading to MindsDB: {e}")
        return False

def create_rag_model_for_pdf(file_name):
    """Create a RAG model using the uploaded PDF."""
    
    try:
        mindsdb_service = MindsDBService()
        
        if not mindsdb_service._ensure_connection():
            print("❌ Could not connect to MindsDB")
            return False
        
        print("✅ Connected to MindsDB")
        
        # First, test if we can query the uploaded file
        test_query = f"SELECT * FROM files.{file_name} LIMIT 1"
        print(f"🔍 Testing file access: {test_query}")
        
        try:
            result = mindsdb_service.connection.query(test_query)
            print("✅ File is accessible in MindsDB")
        except Exception as e:
            print(f"❌ Cannot access file in MindsDB: {e}")
            return False
        
        # Create RAG model
        model_name = f"{file_name}_rag_model"
        
        rag_model_sql = f"""
        CREATE MODEL mindsdb.{model_name}
        FROM files 
            (SELECT * FROM {file_name})
        PREDICT answer
        USING
           engine="rag",
           llm_type="openai",
           input_column='question';
        """
        
        print(f"🤖 Creating RAG model: {model_name}")
        print(f"SQL: {rag_model_sql}")
        
        result = mindsdb_service.connection.query(rag_model_sql)
        print(f"✅ RAG model created successfully: {model_name}")
        
        return model_name
        
    except Exception as e:
        print(f"❌ Error creating RAG model: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_dataset_with_mindsdb_info(model_name, file_name):
    """Update the dataset with MindsDB model information."""
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get dataset 35
        dataset = db.query(Dataset).filter(Dataset.id == 35).first()
        
        if dataset:
            # Update dataset with MindsDB information
            dataset.mindsdb_table_name = model_name
            dataset.mindsdb_database = "mindsdb"
            dataset.ai_processing_status = "ready"
            
            # Update chat context
            if hasattr(dataset, 'chat_context') and dataset.chat_context:
                dataset.chat_context['mindsdb_datasource'] = file_name
                dataset.chat_context['mindsdb_available'] = True
                dataset.chat_context['rag_model'] = model_name
            
            db.commit()
            print(f"✅ Updated dataset 35 with MindsDB info:")
            print(f"   - MindsDB table: {model_name}")
            print(f"   - File name: {file_name}")
            
        else:
            print("❌ Dataset 35 not found")
            
    except Exception as e:
        print(f"❌ Error updating dataset: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main function to process PDF with MindsDB."""
    
    print("🚀 Starting MindsDB PDF processing...")
    
    # Step 1: Upload PDF to MindsDB
    file_name = upload_pdf_to_mindsdb()
    if not file_name:
        return
    
    # Step 2: Create RAG model
    model_name = create_rag_model_for_pdf(file_name)
    if not model_name:
        return
    
    # Step 3: Update dataset with MindsDB info
    update_dataset_with_mindsdb_info(model_name, file_name)
    
    print("✅ MindsDB PDF processing completed successfully!")
    print(f"   - File uploaded as: {file_name}")
    print(f"   - RAG model created: {model_name}")
    print("   - Dataset updated with MindsDB integration")

if __name__ == "__main__":
    main()