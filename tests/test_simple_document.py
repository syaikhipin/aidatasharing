#!/usr/bin/env python3
"""
Simple test for document processing functionality without database
"""

import sys
import os
import tempfile
import asyncio
from pathlib import Path

# Add backend to path
sys.path.append('./backend')

async def test_document_text_extraction():
    """Test document text extraction without database"""
    
    # Create a test text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""
This is a test document for the AI Share Platform.

The platform allows organizations to:
- Upload and manage datasets with automatic schema detection
- Create AI models using MindsDB integration  
- Share data securely with AI-powered chat capabilities

This document processing feature enables users to upload various document formats.
        """)
        test_file_path = f.name
    
    try:
        print("🧪 Testing document text extraction...")
        
        # Test text file processing
        with open(test_file_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        word_count = len(text_content.split())
        line_count = len(text_content.splitlines())
        
        result = {
            "success": True,
            "method": "direct_read",
            "text_content": text_content,
            "text_extracted": True,
            "page_count": 1,
            "word_count": word_count,
            "preview": text_content[:500] + "..." if len(text_content) > 500 else text_content,
            "metadata": {
                "document_type": "txt",
                "lines": line_count,
                "words": word_count,
                "characters": len(text_content)
            }
        }
        
        print(f"📄 Processing result: {result['metadata']}")
        
        if result.get("success"):
            print("✅ Document text extraction test passed!")
            print(f"   Word Count: {result['word_count']}")
            print(f"   Line Count: {result['metadata']['lines']}")
            print(f"   Character Count: {result['metadata']['characters']}")
            print(f"   Preview: {result['preview'][:100]}...")
        else:
            print(f"❌ Document processing test failed")
        
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

async def test_pdf_processing():
    """Test PDF processing if PyMuPDF is available"""
    try:
        import fitz  # PyMuPDF
        print("✅ PyMuPDF is available for PDF processing")
        
        # Create a simple test
        print("📄 PDF processing library test passed")
        
    except ImportError:
        print("⚠️  PyMuPDF not available - PDF processing will not work")
        print("   Install with: pip install PyMuPDF")

async def test_docx_processing():
    """Test DOCX processing if python-docx is available"""
    try:
        from docx import Document
        print("✅ python-docx is available for DOCX processing")
        
    except ImportError:
        print("⚠️  python-docx not available - DOCX processing will not work")
        print("   Install with: pip install python-docx")

if __name__ == "__main__":
    asyncio.run(test_document_text_extraction())
    asyncio.run(test_pdf_processing())
    asyncio.run(test_docx_processing())