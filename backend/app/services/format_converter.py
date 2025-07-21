"""Format Converter Service for Dataset Downloads
Handles conversion between different file formats during download operations
"""

import json
import tempfile
import os
from typing import Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FormatConverter:
    """Service for converting files between different formats"""
    
    def __init__(self):
        self.supported_conversions = {
            'pdf': ['txt', 'json'],
            'csv': ['json', 'excel'],
            'json': ['csv', 'txt'],
            'excel': ['csv', 'json']
        }
    
    async def convert_file(
        self,
        source_path: str,
        source_format: str,
        target_format: str,
        dataset_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Convert a file from one format to another
        
        Args:
            source_path: Path to the source file
            source_format: Source file format (pdf, csv, json, etc.)
            target_format: Target file format
            dataset_metadata: Optional metadata about the dataset
            
        Returns:
            Path to the converted file
        """
        try:
            # Validate conversion is supported
            if not self._is_conversion_supported(source_format, target_format):
                raise ValueError(f"Conversion from {source_format} to {target_format} is not supported")
            
            # If source and target are the same, return original file
            if source_format.lower() == target_format.lower():
                return source_path
            
            # Perform conversion based on source and target formats
            if source_format.lower() == 'pdf':
                return await self._convert_pdf(source_path, target_format, dataset_metadata)
            elif source_format.lower() == 'csv':
                return await self._convert_csv(source_path, target_format, dataset_metadata)
            elif source_format.lower() == 'json':
                return await self._convert_json(source_path, target_format, dataset_metadata)
            elif source_format.lower() == 'excel':
                return await self._convert_excel(source_path, target_format, dataset_metadata)
            else:
                raise ValueError(f"Unsupported source format: {source_format}")
                
        except Exception as e:
            logger.error(f"Failed to convert file from {source_format} to {target_format}: {e}")
            raise
    
    def _is_conversion_supported(self, source_format: str, target_format: str) -> bool:
        """Check if conversion between formats is supported"""
        source_lower = source_format.lower()
        target_lower = target_format.lower()
        
        return (
            source_lower in self.supported_conversions and
            target_lower in self.supported_conversions[source_lower]
        )
    
    async def _convert_pdf(self, source_path: str, target_format: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Convert PDF to other formats"""
        try:
            import fitz  # PyMuPDF
            
            # Extract text from PDF
            doc = fitz.open(source_path)
            text_content = ""
            pages_data = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                text_content += page_text + "\n"
                
                pages_data.append({
                    "page_number": page_num + 1,
                    "text_content": page_text,
                    "char_count": len(page_text)
                })
            
            doc.close()
            
            # Create temporary file for converted content
            temp_dir = tempfile.mkdtemp()
            
            if target_format.lower() == 'txt':
                output_path = os.path.join(temp_dir, "converted.txt")
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                    
            elif target_format.lower() == 'json':
                output_path = os.path.join(temp_dir, "converted.json")
                
                json_data = {
                    "document_info": {
                        "total_pages": len(pages_data),
                        "total_characters": len(text_content),
                        "word_count": len(text_content.split()),
                        "source_format": "pdf",
                        "converted_at": str(datetime.utcnow()),
                        "metadata": metadata or {}
                    },
                    "content": {
                        "full_text": text_content,
                        "pages": pages_data
                    }
                }
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            return output_path
            
        except ImportError:
            raise ValueError("PyMuPDF (fitz) is required for PDF processing")
        except Exception as e:
            logger.error(f"Failed to convert PDF: {e}")
            raise
    
    async def _convert_csv(self, source_path: str, target_format: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Convert CSV to other formats"""
        try:
            import pandas as pd
            
            # Read CSV file
            df = pd.read_csv(source_path)
            temp_dir = tempfile.mkdtemp()
            
            if target_format.lower() == 'json':
                output_path = os.path.join(temp_dir, "converted.json")
                
                json_data = {
                    "document_info": {
                        "total_rows": len(df),
                        "total_columns": len(df.columns),
                        "columns": list(df.columns),
                        "source_format": "csv",
                        "converted_at": str(datetime.utcnow()),
                        "metadata": metadata or {}
                    },
                    "data": df.to_dict('records')
                }
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                    
            elif target_format.lower() == 'excel':
                output_path = os.path.join(temp_dir, "converted.xlsx")
                df.to_excel(output_path, index=False)
            
            return output_path
            
        except ImportError:
            raise ValueError("pandas is required for CSV processing")
        except Exception as e:
            logger.error(f"Failed to convert CSV: {e}")
            raise
    
    async def _convert_json(self, source_path: str, target_format: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Convert JSON to other formats"""
        try:
            import pandas as pd
            
            # Read JSON file
            with open(source_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            temp_dir = tempfile.mkdtemp()
            
            if target_format.lower() == 'csv':
                output_path = os.path.join(temp_dir, "converted.csv")
                
                # Handle different JSON structures
                if isinstance(json_data, list):
                    df = pd.DataFrame(json_data)
                elif isinstance(json_data, dict):
                    if 'data' in json_data and isinstance(json_data['data'], list):
                        df = pd.DataFrame(json_data['data'])
                    else:
                        df = pd.DataFrame([json_data])
                else:
                    raise ValueError("Unsupported JSON structure for CSV conversion")
                
                df.to_csv(output_path, index=False)
                
            elif target_format.lower() == 'txt':
                output_path = os.path.join(temp_dir, "converted.txt")
                
                # Convert JSON to readable text format
                text_content = json.dumps(json_data, indent=2, ensure_ascii=False)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
            
            return output_path
            
        except ImportError:
            raise ValueError("pandas is required for JSON processing")
        except Exception as e:
            logger.error(f"Failed to convert JSON: {e}")
            raise
    
    async def _convert_excel(self, source_path: str, target_format: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Convert Excel to other formats"""
        try:
            import pandas as pd
            
            # Read Excel file
            df = pd.read_excel(source_path)
            temp_dir = tempfile.mkdtemp()
            
            if target_format.lower() == 'csv':
                output_path = os.path.join(temp_dir, "converted.csv")
                df.to_csv(output_path, index=False)
                
            elif target_format.lower() == 'json':
                output_path = os.path.join(temp_dir, "converted.json")
                
                json_data = {
                    "document_info": {
                        "total_rows": len(df),
                        "total_columns": len(df.columns),
                        "columns": list(df.columns),
                        "source_format": "excel",
                        "converted_at": str(datetime.utcnow()),
                        "metadata": metadata or {}
                    },
                    "data": df.to_dict('records')
                }
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            return output_path
            
        except ImportError:
            raise ValueError("pandas is required for Excel processing")
        except Exception as e:
            logger.error(f"Failed to convert Excel: {e}")
            raise
    
    def get_supported_conversions(self) -> Dict[str, List[str]]:
        """Get all supported format conversions"""
        return self.supported_conversions.copy()
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """Clean up temporary files created during conversion"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                # Also try to remove the temp directory if it's empty
                temp_dir = os.path.dirname(file_path)
                try:
                    os.rmdir(temp_dir)
                except OSError:
                    pass  # Directory not empty or other error
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {e}")

# Global instance
format_converter = FormatConverter()