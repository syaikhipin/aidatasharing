#!/usr/bin/env python3
"""
Test script for document processing functionality
"""

import sys
import os
import tempfile
import asyncio
from pathlib import Path

# Add backend to path
sys.path.append('./backend')

from backend.app.services.connector_service import ConnectorService
from backend.app.core.database import SessionLocal

async def test_document_processing():
    """Test document processing with sample files"""
    
    # Create a test text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""
This is a test document for the AI Share Platform.

The platform allows organizations to:
- Upload and manage datasets with automatic schema detection
- Create AI models using MindsDB integration  
- Share data securely with AI-powered chat capabilities
- Monitor usage through comprehensive analytics
- Manage multi-organization access with role-based permissions

This document processing feature enables users to upload PDF, DOCX, DOC, TXT, RTF, and ODT files to create datasets that can be used for AI chat and analysis.

Key features include:
1. Automatic text extraction from various document formats
2. Word and page count analysis
3. Preview generation
4. AI chat model creation for document Q&A
5. Secure sharing with expiration and password protection

The system uses various libraries for document processing:
- PyMuPDF for PDF files
- python-docx for DOCX files
- docx2txt for DOC files
- striprtf for RTF files
- odfpy for ODT files

This enables comprehensive document analysis and AI-powered insights.
        """)
        test_file_path = f.name
    
    try:
        # Initialize service
        db = SessionLocal()
        connector_service = ConnectorService(db)
        
        print("🧪 Testing document processing...")
        
        # Test document processing
        result = await connector_service.process_document(
            file_path=test_file_path,
            original_filename="test_document.txt",
            user_id=1,  # Assuming user ID 1 exists
            organization_id=1,  # Assuming org ID 1 exists
            dataset_name="Test Document Dataset",
            description="Test document for processing functionality"
        )
        
        print(f"📄 Processing result: {result}")
        
        if result.get("success"):
            print("✅ Document processing test passed!")
            print(f"   Dataset ID: {result.get('dataset_id')}")
            print(f"   Document Type: {result.get('document_type')}")
            print(f"   Processing Result: {result.get('processing_result', {}).get('metadata', {})}")
        else:
            print(f"❌ Document processing test failed: {result.get('error')}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test file
        try:
            os.unlink(test_file_path)
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_document_processing())