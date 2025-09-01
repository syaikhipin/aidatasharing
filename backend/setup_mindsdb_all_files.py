#!/usr/bin/env python3
"""
Setup MindsDB file processing for all supported file types.
Supported types: CSV, XLSX, XLS, JSON, TXT, PDF, Parquet
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

# MindsDB supported file extensions
SUPPORTED_EXTENSIONS = {
    '.csv': 'csv',
    '.xlsx': 'xlsx', 
    '.xls': 'xls',
    '.json': 'json',
    '.txt': 'txt',
    '.pdf': 'pdf',
    '.parquet': 'parquet'
}

def get_file_extension(file_path):
    """Get file extension from path."""
    return os.path.splitext(file_path.lower())[1]

def is_supported_file(file_path):
    """Check if file type is supported by MindsDB."""
    ext = get_file_extension(file_path)
    return ext in SUPPORTED_EXTENSIONS

def upload_file_to_mindsdb(full_path, file_name):
    """Upload file to MindsDB files database."""
    
    if not os.path.exists(full_path):
        print(f"❌ File not found at: {full_path}")
        return False
    
    ext = get_file_extension(full_path)
    if not is_supported_file(full_path):
        print(f"❌ Unsupported file type: {ext}")
        return False
    
    print(f"✅ Found supported file: {full_path}")
    
    # Upload to MindsDB via REST API
    mindsdb_url = "http://127.0.0.1:47334"
    
    try:
        # Determine MIME type based on extension
        mime_types = {
            '.csv': 'text/csv',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.json': 'application/json',
            '.txt': 'text/plain',
            '.pdf': 'application/pdf',
            '.parquet': 'application/octet-stream'
        }
        
        mime_type = mime_types.get(ext, 'application/octet-stream')
        
        # Upload file to MindsDB
        with open(full_path, 'rb') as f:
            files = {'file': (file_name + ext, f, mime_type)}
            response = requests.put(
                f"{mindsdb_url}/api/files/{file_name}",
                files=files
            )
        
        if response.status_code == 200:
            print(f"✅ Successfully uploaded {ext} file to MindsDB as '{file_name}'")
            return file_name
        else:
            print(f"❌ Failed to upload file to MindsDB: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error uploading to MindsDB: {e}")
        return False

def create_model_for_file(file_name, file_type):
    """Create appropriate MindsDB model based on file type."""
    
    try:
        mindsdb_service = MindsDBService()
        
        if not mindsdb_service._ensure_connection():
            print("❌ Could not connect to MindsDB")
            return False
        
        print("✅ Connected to MindsDB")
        
        # Test file access
        test_query = f"SELECT * FROM files.{file_name} LIMIT 1"
        print(f"🔍 Testing file access: {test_query}")
        
        try:
            result = mindsdb_service.connection.query(test_query)
            print("✅ File is accessible in MindsDB")
        except Exception as e:
            print(f"❌ Cannot access file in MindsDB: {e}")
            return False
        
        model_name = f"{file_name}_model"
        
        # Create different models based on file type
        if file_type in ['pdf', 'txt']:
            # RAG model for text-based files
            model_sql = f"""
            CREATE MODEL mindsdb.{model_name}
            FROM files 
                (SELECT * FROM {file_name})
            PREDICT answer
            USING
               engine="rag",
               llm_type="openai",
               input_column='question';
            """
            model_type = "RAG"
            
        elif file_type in ['csv', 'xlsx', 'xls', 'json', 'parquet']:
            # Knowledge base for structured data
            model_sql = f"""
            CREATE KNOWLEDGE_BASE mindsdb.{model_name}
            FROM files.{file_name}
            USING
               model='text-embedding-ada-002',
               storage=mindsdb;
            """
            model_type = "Knowledge Base"
        
        else:
            print(f"❌ Unsupported file type for model creation: {file_type}")
            return False
        
        print(f"🤖 Creating {model_type} model: {model_name}")
        print(f"SQL: {model_sql}")
        
        result = mindsdb_service.connection.query(model_sql)
        print(f"✅ {model_type} model created successfully: {model_name}")
        
        return model_name
        
    except Exception as e:
        print(f"❌ Error creating model: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_dataset_with_mindsdb_info(dataset_id, model_name, file_name, file_type):
    """Update dataset with MindsDB model information."""
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        
        if dataset:
            # Update dataset with MindsDB information
            dataset.mindsdb_table_name = model_name
            dataset.mindsdb_database = "mindsdb"
            dataset.ai_processing_status = "ready"
            
            # Update chat context
            if hasattr(dataset, 'chat_context') and dataset.chat_context:
                dataset.chat_context['mindsdb_datasource'] = file_name
                dataset.chat_context['mindsdb_available'] = True
                dataset.chat_context['model_name'] = model_name
                dataset.chat_context['file_type'] = file_type
            
            db.commit()
            print(f"✅ Updated dataset {dataset_id} with MindsDB info:")
            print(f"   - MindsDB model: {model_name}")
            print(f"   - File name: {file_name}")
            print(f"   - File type: {file_type}")
            
        else:
            print(f"❌ Dataset {dataset_id} not found")
            
    except Exception as e:
        print(f"❌ Error updating dataset: {e}")
        db.rollback()
    finally:
        db.close()

def process_all_uploaded_datasets():
    """Process all uploaded datasets that support MindsDB integration."""
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get all datasets that are uploaded files (not web connectors)
        datasets = db.query(Dataset).filter(
            Dataset.file_path.isnot(None),
            Dataset.connector_id.is_(None)
        ).all()
        
        print(f"Found {len(datasets)} uploaded datasets")
        
        storage_base = '/Users/syaikhipin/Documents/program/simpleaisharing/storage'
        
        for dataset in datasets:
            print(f"\n{'='*50}")
            print(f"Processing Dataset {dataset.id}: {dataset.name}")
            print(f"File path: {dataset.file_path}")
            
            full_path = os.path.join(storage_base, dataset.file_path)
            
            if not os.path.exists(full_path):
                print(f"❌ File not found, skipping: {full_path}")
                continue
            
            ext = get_file_extension(dataset.file_path)
            if not is_supported_file(dataset.file_path):
                print(f"❌ Unsupported file type {ext}, skipping")
                continue
            
            file_type = SUPPORTED_EXTENSIONS[ext]
            file_name = f"dataset_{dataset.id}_{file_type}"
            
            print(f"📁 Processing {file_type.upper()} file...")
            
            # Upload to MindsDB
            uploaded_name = upload_file_to_mindsdb(full_path, file_name)
            if not uploaded_name:
                continue
            
            # Create model
            model_name = create_model_for_file(uploaded_name, file_type)
            if not model_name:
                continue
            
            # Update dataset
            update_dataset_with_mindsdb_info(dataset.id, model_name, uploaded_name, file_type)
            
            print(f"✅ Completed processing dataset {dataset.id}")
        
    except Exception as e:
        print(f"❌ Error processing datasets: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def main():
    """Main function to process all supported files with MindsDB."""
    
    print("🚀 Starting MindsDB processing for all supported file types...")
    print(f"Supported types: {', '.join(SUPPORTED_EXTENSIONS.values())}")
    
    process_all_uploaded_datasets()
    
    print("\n✅ MindsDB processing completed!")

if __name__ == "__main__":
    main()