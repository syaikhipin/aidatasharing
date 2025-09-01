#!/usr/bin/env python3
"""
Extract PDF content and update the dataset with proper content preview and MindsDB integration.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.dataset import Dataset
import PyPDF2
import pdfplumber

def extract_pdf_content(file_path):
    """Extract text content from PDF file using multiple methods."""
    content = ""
    
    # Method 1: Try pdfplumber first (better for complex PDFs)
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    content += text + "\n"
        
        if content.strip():
            print("✅ Successfully extracted content using pdfplumber")
            return content.strip()
    except Exception as e:
        print(f"⚠️ pdfplumber failed: {e}")
    
    # Method 2: Fallback to PyPDF2
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    content += text + "\n"
        
        if content.strip():
            print("✅ Successfully extracted content using PyPDF2")
            return content.strip()
    except Exception as e:
        print(f"⚠️ PyPDF2 failed: {e}")
    
    return None

def update_dataset_with_content():
    """Extract PDF content and update dataset 35."""
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Extracting PDF content for dataset 35...")
        
        # Get dataset 35
        dataset = db.query(Dataset).filter(Dataset.id == 35).first()
        
        if not dataset:
            print("❌ Dataset 35 not found")
            return
        
        print(f"Dataset: {dataset.name}")
        print(f"File path: {dataset.file_path}")
        
        # Construct full file path
        storage_base = '/Users/syaikhipin/Documents/program/simpleaisharing/storage'
        full_path = os.path.join(storage_base, dataset.file_path)
        
        if not os.path.exists(full_path):
            print(f"❌ PDF file not found at: {full_path}")
            return
        
        print(f"✅ PDF file found at: {full_path}")
        
        # Extract PDF content
        content = extract_pdf_content(full_path)
        
        if not content:
            print("❌ Could not extract content from PDF")
            return
        
        print(f"✅ Extracted {len(content)} characters of content")
        print(f"Content preview: {content[:200]}...")
        
        # Update dataset with content
        dataset.content_preview = content[:2000]  # Store first 2000 chars as preview
        
        # Create a basic summary
        lines = content.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        # Estimate row and column count (rough approximation for PDF)
        dataset.row_count = len(non_empty_lines)
        dataset.column_count = 1  # Text content is essentially one column
        
        # Update AI processing status
        dataset.ai_processing_status = "content_extracted"
        
        # Create basic schema metadata
        dataset.schema_metadata = {
            "content_type": "text",
            "estimated_pages": len(content) // 3000,  # Rough estimate
            "total_characters": len(content),
            "estimated_words": len(content.split()),
            "extraction_method": "pdfplumber" if "pdfplumber" in str(content) else "PyPDF2"
        }
        
        # Update file metadata
        file_stats = os.stat(full_path)
        dataset.file_metadata = {
            "file_size": file_stats.st_size,
            "content_extracted": True,
            "extraction_timestamp": str(file_stats.st_mtime)
        }
        
        db.commit()
        
        print(f"✅ Updated dataset with extracted content:")
        print(f"   - Content preview: {len(dataset.content_preview)} chars")
        print(f"   - Estimated rows: {dataset.row_count}")
        print(f"   - Schema metadata: {dataset.schema_metadata}")
        
        return content
        
    except Exception as e:
        print(f"❌ Error during content extraction: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    content = update_dataset_with_content()
    if content:
        print("\n" + "="*50)
        print("EXTRACTED CONTENT SAMPLE:")
        print("="*50)
        print(content[:500] + "..." if len(content) > 500 else content)