"""
Metadata Service for Enhanced Dataset Management
Handles dataset schema analysis, data quality metrics, and statistical analysis
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


class MetadataService:
    """Service for analyzing dataset metadata, schema, and generating statistics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def analyze_dataset_schema(self, dataset: Dataset) -> Dict[str, Any]:
        """
        Analyze and return detailed schema information for a dataset
        
        Args:
            dataset: Dataset model instance
            
        Returns:
            Dict with comprehensive schema analysis
        """
        try:
            if not dataset.file_path:
                logger.warning(f"No file path for dataset {dataset.id}")
                return self._get_basic_schema_info(dataset)
            
            file_path = Path(dataset.file_path)
            if not file_path.exists():
                logger.warning(f"File not found: {dataset.file_path}")
                return self._get_basic_schema_info(dataset)
            
            # Analyze based on dataset type
            if dataset.type.value.lower() == 'csv':
                return await self._analyze_csv_schema(file_path, dataset)
            elif dataset.type.value.lower() == 'json':
                return await self._analyze_json_schema(file_path, dataset)
            elif dataset.type.value.lower() in ['excel', 'xlsx', 'xls']:
                return await self._analyze_excel_schema(file_path, dataset)
            elif dataset.type.value.lower() == 'pdf':
                return await self._analyze_pdf_schema(file_path, dataset)
            else:
                return self._get_basic_schema_info(dataset)
                
        except Exception as e:
            logger.error(f"❌ Schema analysis failed for dataset {dataset.id}: {e}")
            return self._get_basic_schema_info(dataset)
    
    async def _analyze_csv_schema(self, file_path: Path, dataset: Dataset) -> Dict[str, Any]:
        """Analyze CSV file schema and structure"""
        try:
            # Read CSV with pandas
            df = pd.read_csv(file_path, nrows=1000)  # Sample first 1000 rows for analysis
            
            schema_info = {
                "file_type": "csv",
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "columns": [],
                "data_types": {},
                "encoding": "utf-8",
                "delimiter": ",",
                "has_header": True,
                "sample_data": df.head(5).to_dict('records'),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            # Analyze each column
            for col in df.columns:
                col_info = {
                    "name": col,
                    "data_type": str(df[col].dtype),
                    "pandas_dtype": str(df[col].dtype),
                    "null_count": int(df[col].isnull().sum()),
                    "non_null_count": int(df[col].count()),
                    "unique_count": int(df[col].nunique()),
                    "completeness": float(df[col].count() / len(df)),
                }
                
                # Add type-specific analysis
                if df[col].dtype in ['int64', 'float64']:
                    col_info.update({
                        "min_value": float(df[col].min()) if not df[col].empty else None,
                        "max_value": float(df[col].max()) if not df[col].empty else None,
                        "mean": float(df[col].mean()) if not df[col].empty else None,
                        "median": float(df[col].median()) if not df[col].empty else None,
                        "std_dev": float(df[col].std()) if not df[col].empty else None,
                        "quartiles": {
                            "q1": float(df[col].quantile(0.25)) if not df[col].empty else None,
                            "q3": float(df[col].quantile(0.75)) if not df[col].empty else None
                        }
                    })
                elif df[col].dtype == 'object':
                    # String/categorical analysis
                    col_info.update({
                        "avg_length": float(df[col].astype(str).str.len().mean()) if not df[col].empty else None,
                        "max_length": int(df[col].astype(str).str.len().max()) if not df[col].empty else None,
                        "min_length": int(df[col].astype(str).str.len().min()) if not df[col].empty else None,
                        "top_values": df[col].value_counts().head(5).to_dict()
                    })
                
                schema_info["columns"].append(col_info)
                schema_info["data_types"][col] = str(df[col].dtype)
            
            return convert_numpy_types(schema_info)
            
        except Exception as e:
            logger.error(f"❌ CSV schema analysis failed: {e}")
            return convert_numpy_types(self._get_basic_schema_info(dataset))
    
    async def _analyze_json_schema(self, file_path: Path, dataset: Dataset) -> Dict[str, Any]:
        """Analyze JSON file schema and structure"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            def analyze_json_structure(obj, depth=0, max_depth=5):
                """Recursively analyze JSON structure"""
                if depth > max_depth:
                    return {"type": "truncated", "reason": "max_depth_reached"}
                
                if isinstance(obj, dict):
                    structure = {"type": "object", "properties": {}}
                    for key, value in obj.items():
                        structure["properties"][key] = analyze_json_structure(value, depth + 1, max_depth)
                    return structure
                elif isinstance(obj, list):
                    if obj:
                        return {
                            "type": "array",
                            "length": len(obj),
                            "item_type": analyze_json_structure(obj[0], depth + 1, max_depth)
                        }
                    return {"type": "array", "length": 0, "item_type": None}
                else:
                    return {"type": type(obj).__name__, "value": str(obj)[:100]}
            
            structure = analyze_json_structure(data)
            
            schema_info = {
                "file_type": "json",
                "structure": structure,
                "top_level_type": type(data).__name__,
                "encoding": "utf-8",
                "total_size_bytes": file_path.stat().st_size,
                "sample_data": str(data)[:500] + "..." if len(str(data)) > 500 else str(data),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            # Count elements
            def count_elements(obj):
                if isinstance(obj, dict):
                    return sum(count_elements(v) for v in obj.values()) + len(obj)
                elif isinstance(obj, list):
                    return sum(count_elements(item) for item in obj) + len(obj)
                else:
                    return 1
            
            schema_info["element_count"] = count_elements(data)
            
            return convert_numpy_types(schema_info)
            
        except Exception as e:
            logger.error(f"❌ JSON schema analysis failed: {e}")
            return convert_numpy_types(self._get_basic_schema_info(dataset))
    
    async def _analyze_excel_schema(self, file_path: Path, dataset: Dataset) -> Dict[str, Any]:
        """Analyze Excel file schema and structure"""
        try:
            # Read Excel file
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            schema_info = {
                "file_type": "excel",
                "sheet_count": len(sheet_names),
                "sheet_names": sheet_names,
                "sheets": {},
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            # Analyze each sheet (limit to first 3 sheets for performance)
            for sheet_name in sheet_names[:3]:
                df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=1000)
                
                sheet_info = {
                    "name": sheet_name,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": df.columns.tolist(),
                    "data_types": {col: str(df[col].dtype) for col in df.columns},
                    "sample_data": df.head(3).to_dict('records')
                }
                
                schema_info["sheets"][sheet_name] = sheet_info
            
            return convert_numpy_types(schema_info)
            
        except Exception as e:
            logger.error(f"❌ Excel schema analysis failed: {e}")
            return convert_numpy_types(self._get_basic_schema_info(dataset))
    
    async def _analyze_pdf_schema(self, file_path: Path, dataset: Dataset) -> Dict[str, Any]:
        """Analyze PDF file structure"""
        try:
            schema_info = {
                "file_type": "pdf",
                "file_size_bytes": file_path.stat().st_size,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            # Try to extract basic PDF info
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                
                schema_info.update({
                    "page_count": len(doc),
                    "has_text": False,
                    "has_images": False,
                    "metadata": doc.metadata
                })
                
                # Check first few pages for content
                text_content = ""
                for page_num in range(min(3, len(doc))):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    if text.strip():
                        schema_info["has_text"] = True
                        text_content += text[:200]  # Sample text
                
                if text_content:
                    schema_info["sample_text"] = text_content
                
                doc.close()
                
            except ImportError:
                logger.warning("PyMuPDF not available for PDF analysis")
                schema_info["note"] = "Limited PDF analysis - PyMuPDF not available"
            
            return convert_numpy_types(schema_info)
            
        except Exception as e:
            logger.error(f"❌ PDF schema analysis failed: {e}")
            return convert_numpy_types(self._get_basic_schema_info(dataset))
    
    def _get_basic_schema_info(self, dataset: Dataset) -> Dict[str, Any]:
        """Get basic schema info from dataset metadata"""
        return {
            "file_type": dataset.type.value if dataset.type else "unknown",
            "size_bytes": dataset.size_bytes,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "columns": dataset.schema_info.get("columns", []) if dataset.schema_info else [],
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "source": "basic_metadata"
        }
    
    async def get_data_quality_metrics(self, dataset: Dataset) -> Dict[str, Any]:
        """
        Calculate comprehensive data quality metrics
        
        Args:
            dataset: Dataset model instance
            
        Returns:
            Dict with data quality scores and analysis
        """
        try:
            if not dataset.file_path or dataset.type.value.lower() not in ['csv', 'excel']:
                return self._get_basic_quality_metrics(dataset)
            
            file_path = Path(dataset.file_path)
            if not file_path.exists():
                return self._get_basic_quality_metrics(dataset)
            
            # Read data for quality analysis
            if dataset.type.value.lower() == 'csv':
                df = pd.read_csv(file_path, nrows=5000)  # Sample for quality analysis
            else:
                df = pd.read_excel(file_path, nrows=5000)
            
            total_cells = df.size
            total_rows = len(df)
            total_cols = len(df.columns)
            
            # Calculate completeness
            null_cells = df.isnull().sum().sum()
            completeness = 1 - (null_cells / total_cells) if total_cells > 0 else 0
            
            # Calculate consistency (basic checks)
            consistency_issues = []
            consistency_score = 1.0
            
            # Check for mixed data types in columns
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Check for mixed numeric/string data
                    numeric_count = pd.to_numeric(df[col], errors='coerce').notna().sum()
                    if 0 < numeric_count < len(df[col].dropna()):
                        consistency_issues.append(f"Mixed data types in column '{col}'")
                        consistency_score -= 0.1
            
            # Calculate accuracy (basic validation)
            accuracy_issues = []
            accuracy_score = 1.0
            
            # Check for obvious data issues
            for col in df.columns:
                if df[col].dtype in ['int64', 'float64']:
                    # Check for extreme outliers
                    if not df[col].empty:
                        q1 = df[col].quantile(0.25)
                        q3 = df[col].quantile(0.75)
                        iqr = q3 - q1
                        outliers = df[(df[col] < q1 - 3*iqr) | (df[col] > q3 + 3*iqr)][col]
                        if len(outliers) > len(df) * 0.05:  # More than 5% outliers
                            accuracy_issues.append(f"High number of outliers in column '{col}'")
                            accuracy_score -= 0.05
            
            # Overall quality score
            overall_score = (completeness * 0.4 + consistency_score * 0.3 + accuracy_score * 0.3)
            
            quality_metrics = {
                "overall_score": round(overall_score, 3),
                "completeness": round(completeness, 3),
                "consistency": round(max(0, consistency_score), 3),
                "accuracy": round(max(0, accuracy_score), 3),
                "issues": consistency_issues + accuracy_issues,
                "details": {
                    "total_cells": total_cells,
                    "null_cells": int(null_cells),
                    "total_rows": total_rows,
                    "total_columns": total_cols,
                    "completeness_by_column": {
                        col: round(1 - (df[col].isnull().sum() / len(df)), 3)
                        for col in df.columns
                    }
                },
                "last_analyzed": datetime.utcnow().isoformat()
            }
            
            return convert_numpy_types(quality_metrics)
            
        except Exception as e:
            logger.error(f"❌ Quality metrics calculation failed for dataset {dataset.id}: {e}")
            return convert_numpy_types(self._get_basic_quality_metrics(dataset))
    
    def _get_basic_quality_metrics(self, dataset: Dataset) -> Dict[str, Any]:
        """Get basic quality metrics from existing metadata"""
        return {
            "overall_score": 0.8,  # Default assumption
            "completeness": 0.9,
            "consistency": 0.8,
            "accuracy": 0.8,
            "issues": ["Limited quality analysis - file not accessible"],
            "last_analyzed": datetime.utcnow().isoformat(),
            "source": "basic_estimation"
        }
    
    async def generate_column_statistics(self, dataset: Dataset) -> Dict[str, Any]:
        """
        Generate detailed statistics for each column
        
        Args:
            dataset: Dataset model instance
            
        Returns:
            Dict with per-column statistical analysis
        """
        try:
            if not dataset.file_path or dataset.type.value.lower() not in ['csv', 'excel']:
                return self._get_basic_column_stats(dataset)
            
            file_path = Path(dataset.file_path)
            if not file_path.exists():
                return self._get_basic_column_stats(dataset)
            
            # Read data for statistical analysis
            if dataset.type.value.lower() == 'csv':
                df = pd.read_csv(file_path, nrows=10000)  # Sample for stats
            else:
                df = pd.read_excel(file_path, nrows=10000)
            
            column_stats = {}
            
            for col in df.columns:
                col_stats = {
                    "column_name": col,
                    "data_type": str(df[col].dtype),
                    "total_count": len(df),
                    "non_null_count": int(df[col].count()),
                    "null_count": int(df[col].isnull().sum()),
                    "unique_count": int(df[col].nunique()),
                    "completeness": round(df[col].count() / len(df), 3)
                }
                
                # Numeric column statistics
                if df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                    if not df[col].empty:
                        col_stats.update({
                            "min": float(df[col].min()),
                            "max": float(df[col].max()),
                            "mean": round(float(df[col].mean()), 3),
                            "median": round(float(df[col].median()), 3),
                            "std_dev": round(float(df[col].std()), 3),
                            "variance": round(float(df[col].var()), 3),
                            "quartiles": {
                                "q1": round(float(df[col].quantile(0.25)), 3),
                                "q2": round(float(df[col].quantile(0.5)), 3),
                                "q3": round(float(df[col].quantile(0.75)), 3)
                            },
                            "skewness": round(float(df[col].skew()), 3),
                            "kurtosis": round(float(df[col].kurtosis()), 3)
                        })
                
                # String/categorical column statistics
                elif df[col].dtype == 'object':
                    col_stats.update({
                        "avg_length": round(df[col].astype(str).str.len().mean(), 2) if not df[col].empty else 0,
                        "max_length": int(df[col].astype(str).str.len().max()) if not df[col].empty else 0,
                        "min_length": int(df[col].astype(str).str.len().min()) if not df[col].empty else 0,
                        "most_frequent": df[col].mode().iloc[0] if not df[col].mode().empty else None,
                        "top_values": df[col].value_counts().head(10).to_dict()
                    })
                
                # Boolean column statistics
                elif df[col].dtype == 'bool':
                    value_counts = df[col].value_counts()
                    col_stats.update({
                        "true_count": int(value_counts.get(True, 0)),
                        "false_count": int(value_counts.get(False, 0)),
                        "true_percentage": round(value_counts.get(True, 0) / len(df) * 100, 2)
                    })
                
                column_stats[col] = col_stats
            
            return convert_numpy_types({
                "columns": column_stats,
                "total_columns": len(df.columns),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "sample_size": len(df)
            })
            
        except Exception as e:
            logger.error(f"❌ Column statistics generation failed for dataset {dataset.id}: {e}")
            return convert_numpy_types(self._get_basic_column_stats(dataset))
    
    def _get_basic_column_stats(self, dataset: Dataset) -> Dict[str, Any]:
        """Get basic column statistics from existing metadata"""
        column_stats = {}
        
        if dataset.schema_info and "columns" in dataset.schema_info:
            for col in dataset.schema_info["columns"]:
                column_stats[col] = {
                    "column_name": col,
                    "data_type": "unknown",
                    "total_count": dataset.row_count or 0,
                    "analysis_source": "basic_metadata"
                }
        
        return {
            "columns": column_stats,
            "total_columns": dataset.column_count or 0,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "source": "basic_metadata"
        }
    
    async def update_dataset_metadata(self, dataset_id: int) -> Dict[str, Any]:
        """
        Update all metadata for a dataset
        
        Args:
            dataset_id: Dataset ID to update
            
        Returns:
            Dict with update results
        """
        try:
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                raise Exception(f"Dataset {dataset_id} not found")
            
            logger.info(f"🔄 Updating metadata for dataset {dataset_id}")
            
            # Generate all metadata
            schema_metadata = await self.analyze_dataset_schema(dataset)
            quality_metrics = await self.get_data_quality_metrics(dataset)
            column_statistics = await self.generate_column_statistics(dataset)
            
            # Update dataset record
            dataset.schema_metadata = schema_metadata
            dataset.quality_metrics = quality_metrics
            dataset.column_statistics = column_statistics
            dataset.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"✅ Metadata updated for dataset {dataset_id}")
            
            return {
                "dataset_id": dataset_id,
                "status": "success",
                "schema_metadata": schema_metadata,
                "quality_metrics": quality_metrics,
                "column_statistics": column_statistics,
                "updated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to update metadata for dataset {dataset_id}: {e}")
            return {
                "dataset_id": dataset_id,
                "status": "error",
                "error": str(e),
                "updated_at": datetime.utcnow().isoformat()
            }