"""
Preview Service for Enhanced Dataset Management
Handles dataset content preview generation without loading full files
"""

import pandas as pd
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from app.models.dataset import Dataset

logger = logging.getLogger(__name__)


def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif pd.isna(obj):
        return None
    return obj


class PreviewService:
    """Service for generating dataset content previews"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def generate_preview_data(
        self, 
        dataset: Dataset, 
        rows: int = 20,
        include_stats: bool = True,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Generate preview data for a dataset without loading the full file
        
        Args:
            dataset: Dataset model instance
            rows: Number of rows to include in preview
            include_stats: Whether to include basic statistics
            
        Returns:
            Dict with preview data and metadata
        """
        try:
            # First try to get preview from FileUpload metadata (universal upload system)
            file_upload_preview = await self._get_file_upload_preview(dataset, rows, include_stats)
            if file_upload_preview:
                return file_upload_preview
            
            # Fallback to file-based preview for legacy datasets
            file_path = None
            if dataset.source_url:
                # Handle both relative and absolute paths
                if dataset.source_url.startswith('./'):
                    file_path = Path(dataset.source_url[2:])  # Remove './' prefix
                elif dataset.source_url.startswith('/'):
                    file_path = Path(dataset.source_url)
                else:
                    # Try relative to storage directories
                    potential_paths = [
                        Path(dataset.source_url),
                        Path("../storage") / dataset.source_url,
                        Path("storage") / dataset.source_url,
                        Path("../storage/uploads") / dataset.source_url
                    ]
                    for potential_path in potential_paths:
                        if potential_path.exists():
                            file_path = potential_path
                            break
            elif dataset.file_path:
                file_path = Path(dataset.file_path)
                
            # If we found a valid file path, try to generate preview
            if file_path and file_path.exists():
                logger.info(f"📁 Generating preview from file: {file_path}")
                
                # Generate preview based on file type
                if dataset.type.value.lower() == 'csv':
                    return await self._generate_csv_preview(file_path, dataset, rows, include_stats)
                elif dataset.type.value.lower() == 'json':
                    return await self._generate_json_preview(file_path, dataset, rows, include_stats)
                elif dataset.type.value.lower() in ['excel', 'xlsx', 'xls']:
                    return await self._generate_excel_preview(file_path, dataset, rows, include_stats)
                elif dataset.type.value.lower() == 'pdf':
                    return await self._generate_pdf_preview(file_path, dataset, rows, include_stats)
                elif dataset.type.value.lower() == 'image':
                    return await self._generate_image_preview(file_path, dataset, rows, include_stats)
            else:
                logger.warning(f"⚠️ File not found for dataset {dataset.id}: {dataset.source_url}")
                
            # If no file found or unsupported format, try to load from existing data
            return await self._generate_preview_from_metadata(dataset, rows, include_stats)
                
        except Exception as e:
            logger.error(f"❌ Preview generation failed for dataset {dataset.id}: {e}")
            return self._get_cached_preview(dataset, rows)
    
    async def _generate_csv_preview(
        self, 
        file_path: Path, 
        dataset: Dataset, 
        rows: int,
        include_stats: bool,
        page: int = 1
    ) -> Dict[str, Any]:
        """Generate preview for CSV files with pagination support"""
        try:
            # Calculate skip rows for pagination
            skip_rows = (page - 1) * rows if page > 1 else 0
            
            # For stats and total count, we need to read the file once
            if include_stats or page > 1:
                # Get total row count for pagination info
                total_rows = dataset.row_count
                if not total_rows:
                    # Count rows efficiently without loading the whole file
                    with open(file_path, 'r') as f:
                        total_rows = sum(1 for _ in f) - 1  # Subtract header row
            
            # Read only the required page of rows for preview
            if page > 1:
                # Skip to the requested page
                df = pd.read_csv(file_path, skiprows=range(1, skip_rows + 1), nrows=rows)
            else:
                # First page, no need to skip
                df = pd.read_csv(file_path, nrows=rows)
            
            preview_data = {
                "type": "tabular",
                "format": "csv",
                "headers": df.columns.tolist(),
                "rows": df.to_dict('records'),
                "total_rows_in_preview": len(df),
                "estimated_total_rows": dataset.row_count or total_rows or "unknown",
                "total_columns": len(df.columns),
                "is_sample": True,
                "sample_info": {
                    "method": "pagination" if page > 1 else "head",
                    "rows_requested": rows,
                    "rows_returned": len(df),
                    "page": page,
                    "total_pages": int(total_rows / rows) + 1 if isinstance(total_rows, int) and total_rows > 0 else 1
                },
                "column_types": {col: str(df[col].dtype) for col in df.columns},
                "generated_at": datetime.utcnow().isoformat()
            }
            
            if include_stats:
                preview_data["basic_stats"] = self._calculate_preview_stats(df)
            
            # Add data quality indicators
            preview_data["quality_indicators"] = {
                "has_null_values": df.isnull().any().any(),
                "null_columns": df.columns[df.isnull().any()].tolist(),
                "completeness_by_column": {
                    col: round(1 - (df[col].isnull().sum() / len(df)), 3)
                    for col in df.columns
                }
            }
            
            return convert_numpy_types(preview_data)
            
        except Exception as e:
            logger.error(f"❌ CSV preview generation failed: {e}")
            return convert_numpy_types(self._get_error_preview(dataset, str(e)))
    
    async def _generate_json_preview(
        self, 
        file_path: Path, 
        dataset: Dataset, 
        rows: int,
        include_stats: bool,
        page: int = 1
    ) -> Dict[str, Any]:
        """Generate preview for JSON files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            preview_data = {
                "type": "json",
                "format": "json",
                "structure_type": type(data).__name__,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            if isinstance(data, list):
                # Array of objects with pagination support
                start_idx = (page - 1) * rows if page > 1 else 0
                end_idx = start_idx + rows
                preview_items = data[start_idx:end_idx] if len(data) > start_idx else []
                total_pages = (len(data) + rows - 1) // rows  # Ceiling division
                preview_data.update({
                    "items": preview_items,
                    "total_items_in_preview": len(preview_items),
                    "estimated_total_items": len(data),
                    "is_sample": len(data) > rows,
                    "sample_info": {
                        "method": "slice",
                        "items_requested": rows,
                        "items_returned": len(preview_items)
                    }
                })
                
                # If items are objects, analyze structure
                if preview_items and isinstance(preview_items[0], dict):
                    all_keys = set()
                    for item in preview_items:
                        if isinstance(item, dict):
                            all_keys.update(item.keys())
                    
                    preview_data["common_fields"] = list(all_keys)
                    preview_data["field_types"] = {}
                    
                    # Analyze field types from sample
                    for key in all_keys:
                        types = set()
                        for item in preview_items[:10]:  # Sample first 10 items
                            if isinstance(item, dict) and key in item:
                                types.add(type(item[key]).__name__)
                        preview_data["field_types"][key] = list(types)
            
            elif isinstance(data, dict):
                # Single object
                preview_data.update({
                    "content": data,
                    "keys": list(data.keys()) if isinstance(data, dict) else [],
                    "is_sample": False
                })
            
            else:
                # Primitive value
                preview_data.update({
                    "content": data,
                    "value_type": type(data).__name__,
                    "is_sample": False
                })
            
            return convert_numpy_types(preview_data)
            
        except Exception as e:
            logger.error(f"❌ JSON preview generation failed: {e}")
            return convert_numpy_types(self._get_error_preview(dataset, str(e)))
    
    async def _generate_excel_preview(
        self, 
        file_path: Path, 
        dataset: Dataset, 
        rows: int,
        include_stats: bool,
        page: int = 1
    ) -> Dict[str, Any]:
        """Generate preview for Excel files"""
        try:
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            preview_data = {
                "type": "excel",
                "format": "excel",
                "sheet_count": len(sheet_names),
                "sheet_names": sheet_names,
                "sheets": {},
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Preview first sheet or up to 3 sheets
            sheets_to_preview = sheet_names[:min(3, len(sheet_names))]
            
            for sheet_name in sheets_to_preview:
                # Calculate skip rows for pagination
                skip_rows = (page - 1) * rows if page > 1 else 0
                
                # Get total row count for pagination info
                total_rows = dataset.row_count
                if not total_rows:
                    try:
                        # Count rows in the sheet without loading all data
                        xl = pd.ExcelFile(file_path)
                        total_rows = xl.book.sheet_by_name(sheet_name).nrows - 1  # Subtract header row
                    except:
                        # Fallback if counting fails
                        total_rows = None
                
                # Read only the required page of rows for preview
                if page > 1:
                    # Skip to the requested page
                    df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=range(1, skip_rows + 1), nrows=rows)
                else:
                    # First page, no need to skip
                    df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=rows)
                
                sheet_preview = {
                    "name": sheet_name,
                    "headers": df.columns.tolist(),
                    "rows": df.to_dict('records'),
                    "total_rows_in_preview": len(df),
                    "total_columns": len(df.columns),
                    "column_types": {col: str(df[col].dtype) for col in df.columns},
                    "is_sample": True,
                    "sample_info": {
                        "method": "pagination" if page > 1 else "head",
                        "rows_requested": rows,
                        "rows_returned": len(df),
                        "page": page,
                        "total_pages": int(total_rows / rows) + 1 if isinstance(total_rows, int) and total_rows > 0 else 1
                    }
                }
                
                if include_stats:
                    sheet_preview["basic_stats"] = self._calculate_preview_stats(df)
                
                preview_data["sheets"][sheet_name] = sheet_preview
            
            # Set primary sheet (usually first sheet)
            if sheet_names:
                preview_data["primary_sheet"] = sheet_names[0]
                if sheet_names[0] in preview_data["sheets"]:
                    preview_data["primary_data"] = preview_data["sheets"][sheet_names[0]]
            
            return convert_numpy_types(preview_data)
            
        except Exception as e:
            logger.error(f"❌ Excel preview generation failed: {e}")
            return convert_numpy_types(self._get_error_preview(dataset, str(e)))
    
    async def _generate_image_preview(
        self, 
        file_path: Path, 
        dataset: Dataset, 
        rows: int,
        include_stats: bool,
        page: int = 1
    ) -> Dict[str, Any]:
        """Generate preview for image files"""
        try:
            preview_data = {
                "type": "image",
                "format": "image",
                "file_size_bytes": file_path.stat().st_size,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            try:
                from PIL import Image
                with Image.open(file_path) as img:
                    preview_data.update({
                        "dimensions": {
                            "width": img.width,
                            "height": img.height
                        },
                        "image_format": img.format,
                        "color_mode": img.mode,
                        "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                    })
                    
                    # Extract EXIF data if available
                    exif_data = {}
                    if hasattr(img, '_getexif') and img._getexif():
                        try:
                            raw_exif = img._getexif()
                            if raw_exif:
                                # Convert only basic EXIF data to avoid serialization issues
                                for key, value in raw_exif.items():
                                    if isinstance(value, (str, int, float)) and len(str(value)) < 100:
                                        exif_data[str(key)] = str(value)
                        except Exception:
                            pass  # EXIF extraction can fail
                    
                    if exif_data:
                        preview_data["exif_data"] = exif_data
                
                # Add image metadata summary
                preview_data["image_metadata"] = {
                    "format": preview_data.get("image_format", "unknown"),
                    "dimensions": preview_data.get("dimensions", {}),
                    "color_mode": preview_data.get("color_mode", "unknown"),
                    "file_size_mb": round(preview_data["file_size_bytes"] / (1024 * 1024), 2)
                }
                
            except ImportError:
                preview_data.update({
                    "error": "Image processing not available",
                    "note": "PIL library not installed",
                    "basic_info_only": True
                })
            except Exception as e:
                preview_data.update({
                    "error": f"Failed to process image: {str(e)}",
                    "basic_info_only": True
                })
            
            return convert_numpy_types(preview_data)
            
        except Exception as e:
            logger.error(f"❌ Image preview generation failed: {e}")
            return convert_numpy_types(self._get_error_preview(dataset, str(e)))
    
    async def _generate_pdf_preview(
        self, 
        file_path: Path, 
        dataset: Dataset, 
        rows: int,
        include_stats: bool,
        page: int = 1
    ) -> Dict[str, Any]:
        """Generate preview for PDF files"""
        try:
            preview_data = {
                "type": "pdf",
                "format": "pdf",
                "file_size_bytes": file_path.stat().st_size,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                
                preview_data.update({
                    "page_count": len(doc),
                    "pages": []
                })
                
                # Extract text from pages with pagination support
                total_pages = len(doc)
                start_page = (page - 1) * rows if page > 1 else 0
                end_page = min(start_page + rows, total_pages)
                pages_to_preview = end_page - start_page
                
                # Add pagination info
                preview_data["pagination"] = {
                    "current_page": page,
                    "total_pages": (total_pages + rows - 1) // rows if rows > 0 else 1,
                    "pages_per_view": rows,
                    "total_document_pages": total_pages
                }
                
                for page_num in range(start_page, end_page):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    
                    page_preview = {
                        "page_number": page_num + 1,
                        "text_content": text[:500] + "..." if len(text) > 500 else text,
                        "has_text": bool(text.strip()),
                        "char_count": len(text)
                    }
                    
                    preview_data["pages"].append(page_preview)
                
                doc.close()
                
                # Summary
                total_text = sum(len(page.get("text_content", "")) for page in preview_data["pages"])
                preview_data["summary"] = {
                    "total_pages_previewed": pages_to_preview,
                    "has_extractable_text": any(page.get("has_text", False) for page in preview_data["pages"]),
                    "total_preview_chars": total_text
                }
                
            except ImportError:
                preview_data.update({
                    "error": "PDF text extraction not available",
                    "note": "PyMuPDF library not installed",
                    "basic_info_only": True
                })
            
            return convert_numpy_types(preview_data)
            
        except Exception as e:
            logger.error(f"❌ PDF preview generation failed: {e}")
            return convert_numpy_types(self._get_error_preview(dataset, str(e)))
    
    def _calculate_preview_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistics for preview data"""
        try:
            stats = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "numeric_columns": [],
                "text_columns": [],
                "null_counts": {}
            }
            
            for col in df.columns:
                null_count = df[col].isnull().sum()
                stats["null_counts"][col] = int(null_count)
                
                if df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                    stats["numeric_columns"].append({
                        "name": col,
                        "min": float(df[col].min()) if not df[col].empty else None,
                        "max": float(df[col].max()) if not df[col].empty else None,
                        "mean": round(float(df[col].mean()), 3) if not df[col].empty else None
                    })
                elif df[col].dtype == 'object':
                    stats["text_columns"].append({
                        "name": col,
                        "unique_count": int(df[col].nunique()),
                        "most_common": df[col].mode().iloc[0] if not df[col].mode().empty else None
                    })
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Preview stats calculation failed: {e}")
            return {"error": str(e)}
    
    def _get_cached_preview(self, dataset: Dataset, rows: int) -> Dict[str, Any]:
        """Get preview from cached dataset metadata"""
        if dataset.preview_data:
            cached_preview = dataset.preview_data.copy()
            cached_preview.update({
                "source": "cached",
                "last_generated": cached_preview.get("preview_generated_at", "unknown"),
                "note": "Using cached preview data"
            })
            # Ensure we have proper structure for UI
            # Handle different field names used in preview data
            if not cached_preview.get("rows") and cached_preview.get("sample_rows"):
                cached_preview["rows"] = cached_preview["sample_rows"]
                cached_preview["total_rows_in_preview"] = len(cached_preview["sample_rows"])
            elif not cached_preview.get("rows") and cached_preview.get("headers"):
                # Generate empty rows structure for UI
                cached_preview["rows"] = []
                cached_preview["total_rows_in_preview"] = 0
                cached_preview["note"] = "Headers available but no sample data"
            return cached_preview
        
        # Fallback to basic info with proper structure for UI
        return {
            "type": "basic",
            "format": dataset.type.value if dataset.type else "unknown",
            "message": "Preview not available - no file path found",
            "headers": [],
            "rows": [],
            "total_rows_in_preview": 0,
            "basic_info": {
                "name": dataset.name,
                "size_bytes": dataset.size_bytes,
                "row_count": dataset.row_count,
                "column_count": dataset.column_count,
                "created_at": dataset.created_at.isoformat() if dataset.created_at else None
            },
            "generated_at": datetime.utcnow().isoformat(),
            "source": "basic_metadata"
        }
    
    def _get_error_preview(self, dataset: Dataset, error_message: str) -> Dict[str, Any]:
        """Get error preview when generation fails"""
        return {
            "type": "error",
            "format": dataset.type.value if dataset.type else "unknown",
            "error": error_message,
            "message": "Preview generation failed",
            "basic_info": {
                "name": dataset.name,
                "size_bytes": dataset.size_bytes,
                "row_count": dataset.row_count,
                "column_count": dataset.column_count
            },
            "generated_at": datetime.utcnow().isoformat(),
            "source": "error_fallback"
        }
    
    async def update_dataset_preview(self, dataset_id: int, rows: int = 20, page: int = 1) -> Dict[str, Any]:
        """
        Update cached preview data for a dataset
        
        Args:
            dataset_id: Dataset ID to update
            rows: Number of rows to include in preview
            page: Page number for pagination
            
        Returns:
            Dict with update results
        """
        try:
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                raise Exception(f"Dataset {dataset_id} not found")
            
            logger.info(f"🔄 Updating preview for dataset {dataset_id}")
            
            # Generate new preview
            preview_data = await self.generate_preview_data(dataset, rows, include_stats=True, page=page)
            
            # Update dataset record
            dataset.preview_data = preview_data
            dataset.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"✅ Preview updated for dataset {dataset_id}")
            
            return {
                "dataset_id": dataset_id,
                "status": "success",
                "preview_data": preview_data,
                "updated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to update preview for dataset {dataset_id}: {e}")
            return {
                "dataset_id": dataset_id,
                "status": "error",
                "error": str(e),
                "updated_at": datetime.utcnow().isoformat()
            }
    
    def get_preview_formats(self, dataset: Dataset) -> List[str]:
        """
        Get available preview formats for a dataset
        
        Args:
            dataset: Dataset model instance
            
        Returns:
            List of available preview formats
        """
        base_formats = ["json"]  # All datasets can be previewed as JSON
        
        if dataset.type.value.lower() in ['csv', 'excel']:
            base_formats.extend(["table", "raw"])
        elif dataset.type.value.lower() == 'json':
            base_formats.extend(["formatted", "raw"])
        elif dataset.type.value.lower() == 'pdf':
            base_formats.extend(["text", "pages"])
        
        return base_formats
    async def _generate_preview_from_metadata(self, dataset: Dataset, rows: int, include_stats: bool) -> Dict[str, Any]:
        """Generate preview from dataset metadata when file is not available"""
        try:
            # Check if we have sample data in schema_info
            if dataset.schema_info and isinstance(dataset.schema_info, dict):
                sample_data = dataset.schema_info.get("sample_data", [])
                headers = dataset.schema_info.get("headers", [])
                
                if sample_data and headers:
                    # Use existing sample data
                    preview_data = {
                        "type": "tabular",
                        "format": dataset.type.value.lower(),
                        "headers": headers,
                        "rows": sample_data[:rows],
                        "total_rows_in_preview": min(len(sample_data), rows),
                        "estimated_total_rows": dataset.row_count or len(sample_data),
                        "total_columns": len(headers),
                        "is_sample": True,
                        "sample_info": {
                            "method": "metadata_sample",
                            "rows_requested": rows,
                            "rows_returned": min(len(sample_data), rows)
                        },
                        "generated_at": datetime.utcnow().isoformat(),
                        "source": "metadata_sample",
                        "note": "Generated from stored sample data"
                    }
                    
                    if include_stats:
                        # Generate basic stats from sample data
                        preview_data["basic_stats"] = {
                            "row_count": min(len(sample_data), rows),
                            "column_count": len(headers),
                            "sample_based": True
                        }
                    
                    return convert_numpy_types(preview_data)
            
            # Check if dataset has preview_data field with useful content
            if dataset.preview_data and isinstance(dataset.preview_data, dict):
                preview = dataset.preview_data.copy()
                if preview.get("headers"):
                    # Ensure proper structure for UI
                    # Handle different field names
                    if not preview.get("rows") and preview.get("sample_rows"):
                        preview["rows"] = preview["sample_rows"]
                        preview["total_rows_in_preview"] = len(preview["sample_rows"])
                    elif not preview.get("rows"):
                        preview["rows"] = []
                        preview["total_rows_in_preview"] = 0
                        preview["note"] = "Headers available but no sample data found"
                    preview["source"] = "stored_preview"
                    return convert_numpy_types(preview)
            
            # Generate a basic structure for datasets with metadata but no sample data
            headers = []
            if dataset.schema_metadata and isinstance(dataset.schema_metadata, dict):
                columns = dataset.schema_metadata.get("columns", [])
                if columns:
                    headers = columns if isinstance(columns[0], str) else [col.get("name", f"col_{i}") for i, col in enumerate(columns)]
            
            return {
                "type": "metadata",
                "format": dataset.type.value.lower() if dataset.type else "unknown",
                "headers": headers,
                "rows": [],
                "total_rows_in_preview": 0,
                "estimated_total_rows": dataset.row_count or 0,
                "total_columns": len(headers),
                "is_sample": False,
                "message": "Dataset metadata available but no sample data",
                "basic_info": {
                    "name": dataset.name,
                    "size_bytes": dataset.size_bytes,
                    "row_count": dataset.row_count,
                    "column_count": dataset.column_count,
                    "created_at": dataset.created_at.isoformat() if dataset.created_at else None
                },
                "generated_at": datetime.utcnow().isoformat(),
                "source": "metadata_only"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate preview from metadata for dataset {dataset.id}: {e}")
            return self._get_cached_preview(dataset, rows)
    async def _get_file_upload_preview(self, dataset: Dataset, rows: int, include_stats: bool) -> Dict[str, Any]:
        """Generate preview from FileUpload metadata (universal upload system)"""
        from app.models.file_handler import FileUpload
        
        # Get the FileUpload record for this dataset
        file_upload = self.db.query(FileUpload).filter(
            FileUpload.dataset_id == dataset.id
        ).first()
        
        if not file_upload or not file_upload.file_metadata:
            return None
            
        metadata = file_upload.file_metadata
        
        # Create rich preview from stored metadata
        preview_data = {
            "type": metadata.get("type", "basic"),
            "format": metadata.get("format", "unknown"),
            "file_size_bytes": file_upload.file_size,
            "estimated_total_rows": metadata.get("rows", metadata.get("data_rows", 0)),
            "total_columns": len(metadata.get("headers", [])) if metadata.get("headers") else metadata.get("columns", 0),
            "source": "file_upload_metadata",
            "generated_at": datetime.utcnow().isoformat(),
            "file_upload_id": file_upload.id,
            "original_filename": file_upload.original_filename
        }
        
        # Handle different file types based on enhanced metadata
        if metadata.get("type") == "spreadsheet" or file_upload.file_type == "spreadsheet":
            preview_data.update(self._create_spreadsheet_preview(metadata, rows))
        elif metadata.get("type") == "image" or file_upload.file_type == "image":
            preview_data.update(self._create_image_preview(metadata, file_upload))
        elif metadata.get("type") == "document" or file_upload.file_type == "document":
            preview_data.update(self._create_document_preview(metadata, rows))
        elif metadata.get("type") == "json" or metadata.get("structure_type"):
            preview_data.update(self._create_json_preview(metadata, rows))
        else:
            preview_data.update(self._create_basic_preview(metadata, rows))
            
        # Add basic statistics if requested
        if include_stats:
            stats = {
                "row_count": metadata.get("rows", metadata.get("data_rows", 0)),
                "column_count": len(metadata.get("headers", [])) if metadata.get("headers") else metadata.get("columns", 0),
                "numeric_columns": [],
                "text_columns": []
            }
            
            # Enhanced statistics from metadata
            if metadata.get("estimated_data_types"):
                for col, dtype in metadata.get("estimated_data_types", {}).items():
                    if "int" in str(dtype).lower() or "float" in str(dtype).lower():
                        stats["numeric_columns"].append(col)
                    else:
                        stats["text_columns"].append(col)
            elif metadata.get("column_statistics"):
                # Categorize columns by type from column statistics
                for col, col_stats in metadata.get("column_statistics", {}).items():
                    col_type = col_stats.get("inferred_type", "unknown")
                    if col_type in ["numeric", "integer", "float"]:
                        stats["numeric_columns"].append(col)
                    else:
                        stats["text_columns"].append(col)
                        
            preview_data["basic_stats"] = stats
                    
        return preview_data
    
    def _create_image_preview(self, metadata: Dict[str, Any], file_upload) -> Dict[str, Any]:
        """Create preview for image data from metadata"""
        preview = {
            "content_type": "image",
            "image_metadata": metadata.get("image_info", {})
        }
        
        # Add specific image fields from file_upload if available
        if file_upload:
            preview["dimensions"] = {
                "width": file_upload.image_width,
                "height": file_upload.image_height
            }
            preview["format"] = file_upload.image_format
            preview["color_mode"] = file_upload.color_mode
            
        # Add EXIF data if available
        if metadata.get("exif"):
            preview["exif_data"] = metadata["exif"]
            
        return preview
    
    def _create_spreadsheet_preview(self, metadata: Dict[str, Any], rows: int) -> Dict[str, Any]:
        """Create preview for spreadsheet data from metadata"""
        sample_data = metadata.get("sample_data", [])
        
        preview = {
            "headers": metadata.get("headers", []),
            "rows": sample_data[:rows],  # Normalize to 'rows' field
            "total_rows_in_preview": min(len(sample_data), rows),
            "has_header": metadata.get("has_header", True),
            "delimiter": metadata.get("delimiter", ","),
            "encoding": metadata.get("encoding", "utf-8")
        }
        
        # Add column types if available
        if metadata.get("estimated_data_types"):
            preview["column_types"] = metadata["estimated_data_types"]
            
        return preview
    
    def _create_document_preview(self, metadata: Dict[str, Any], rows: int) -> Dict[str, Any]:
        """Create preview for document data from metadata"""
        preview = {
            "content_type": "document",
            "lines": metadata.get("lines", 0),
            "characters": metadata.get("characters", 0),
            "words": metadata.get("words", 0),
            "preview": metadata.get("preview", "")[:1000]  # Limit preview length
        }
        
        if metadata.get("encoding"):
            preview["encoding"] = metadata["encoding"]
            
        return preview
    
    def _create_json_preview(self, metadata: Dict[str, Any], rows: int) -> Dict[str, Any]:
        """Create preview for JSON data from metadata"""
        preview = {
            "structure_type": metadata.get("structure_type", "unknown"),
            "top_level_keys": metadata.get("top_level_keys", []),
            "valid_json": metadata.get("valid_json", True)
        }
        
        # Add structure analysis if available
        if metadata.get("structure_analysis"):
            preview["structure_analysis"] = metadata["structure_analysis"]
            
        # Add preview content if available
        if metadata.get("preview"):
            preview["content_preview"] = metadata["preview"]
            
        return preview
    
    def _create_basic_preview(self, metadata: Dict[str, Any], rows: int) -> Dict[str, Any]:
        """Create basic preview for other file types"""
        return {
            "file_format": metadata.get("format", "unknown"),
            "size_bytes": metadata.get("size_bytes", 0),
            "basic_info": {
                "filename": metadata.get("filename", "unknown"),
                "type": metadata.get("type", "unknown"),
                "mindsdb_compatible": metadata.get("mindsdb_compatible", False)
            }
        }