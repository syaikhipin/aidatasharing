from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Body
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Dict, Any
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.dataset import Dataset, DatasetType, DatasetStatus
from app.models.organization import DataSharingLevel
from app.schemas.dataset import (
    DatasetCreate, DatasetUpdate, DatasetResponse, 
    DatasetUpload, DatasetStats, DatasetAccessLog
)
from app.services.data_sharing import DataSharingService
from app.services.mindsdb import mindsdb_service
from app.services.storage import storage_service
from app.services.metadata import MetadataService
from app.services.preview import PreviewService
import json
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[DatasetResponse])
async def get_datasets(
    skip: int = 0,
    limit: int = 100,
    sharing_level: Optional[DataSharingLevel] = None,
    dataset_type: Optional[DatasetType] = None,
    include_inactive: bool = False,
    include_deleted: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get datasets accessible to the current user within their organization."""
    if not current_user.organization_id:
        # Return empty list for users without organizations
        return []
    
    data_service = DataSharingService(db)
    datasets = data_service.get_accessible_datasets(
        user=current_user,
        sharing_level=sharing_level,
        include_inactive=include_inactive,
        include_deleted=include_deleted
    )
    
    # Apply additional filters
    filtered_datasets = []
    for dataset in datasets:
        # Filter by type if specified
        if dataset_type and dataset.type != dataset_type:
            continue
        filtered_datasets.append(dataset)
    
    # Apply pagination
    return filtered_datasets[skip:skip + limit]

@router.post("/", response_model=DatasetResponse, status_code=201)
async def create_dataset(
    dataset_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new dataset within the user's organization."""
    # First validate the input data (422 errors)
    name = dataset_data.get("name")
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dataset name is required"
        )
    
    # Then check authorization (403 errors)
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must be part of an organization to create datasets"
        )
    
    # Map data_format to type if provided
    data_format = dataset_data.get("data_format", "CSV")
    dataset_type = DatasetType.CSV if data_format.upper() == "CSV" else DatasetType.JSON
    
    # Extract sharing level
    sharing_level_str = dataset_data.get("sharing_level", "PRIVATE")
    try:
        sharing_level = DataSharingLevel(sharing_level_str)
    except ValueError:
        sharing_level = DataSharingLevel.PRIVATE
    
    # Build schema info from test data
    schema_info = {}
    if "columns" in dataset_data:
        schema_info["columns"] = dataset_data["columns"]
    if "row_count" in dataset_data:
        schema_info["row_count"] = dataset_data["row_count"]
    
    # Generate basic metadata for programmatically created datasets
    columns = dataset_data.get("columns", [])
    row_count = dataset_data.get("row_count", 0)
    
    schema_metadata = {
        "columns": columns,
        "data_types": {},
        "programmatically_created": True,
        "created_at": datetime.utcnow().isoformat()
    }
    
    quality_metrics = {
        "overall_score": 0.9,  # Default good score for programmatic creation
        "completeness": 1.0,
        "consistency": 1.0,
        "accuracy": 0.9,
        "issues": [],
        "last_analyzed": datetime.utcnow().isoformat()
    }
    
    column_statistics = {}
    for col in columns:
        column_statistics[col] = {
            "data_type": "unknown",
            "non_null_count": row_count,
            "null_count": 0,
            "unique_count": "unknown"
        }
    
    preview_data = {
        "headers": columns,
        "sample_rows": [],
        "total_rows": row_count,
        "is_sample": False,
        "preview_generated_at": datetime.utcnow().isoformat()
    }

    # Create dataset with organization context
    db_dataset = Dataset(
        name=name,
        description=dataset_data.get("description"),
        type=dataset_type,
        status=DatasetStatus.ACTIVE,
        owner_id=current_user.id,
        organization_id=current_user.organization_id,
        department_id=current_user.department_id,
        sharing_level=sharing_level,
        source_url=dataset_data.get("source_url"),
        connector_id=dataset_data.get("connector_id"),
        schema_info=schema_info if schema_info else None,
        allow_download=True,
        allow_api_access=True,
        row_count=row_count,
        column_count=len(columns),
        # Enhanced metadata fields
        schema_metadata=schema_metadata,
        quality_metrics=quality_metrics,
        column_statistics=column_statistics,
        preview_data=preview_data,
        download_count=0,
        last_downloaded_at=None
    )
    
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    
    return db_dataset

@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific dataset if accessible to the user."""
    data_service = DataSharingService(db)
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Check access permissions
    if not data_service.can_access_dataset(current_user, dataset):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this dataset"
        )
    
    # Log access
    data_service.log_access(
        user=current_user,
        dataset=dataset,
        access_type="view"
    )
    
    return dataset

@router.put("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: int,
    dataset_update: DatasetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a dataset (only owner can update)."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Only owner or org admin can update
    if dataset.owner_id != current_user.id and not current_user.is_superuser:
        if current_user.role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only dataset owner or organization admin can update"
            )
    
    # Update fields
    for field, value in dataset_update.dict(exclude_unset=True).items():
        setattr(dataset, field, value)
    
    db.commit()
    db.refresh(dataset)
    
    return dataset

@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    force_delete: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a dataset (only owner can delete). Use force_delete=true for hard delete."""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.is_deleted == False
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or already deleted"
        )
    
    # Check if user is owner or admin
    if dataset.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete your own datasets"
        )
    
    # Clean up associated ML models first
    try:
        ml_cleanup_result = mindsdb_service.delete_dataset_models(dataset_id)
        logger.info(f"ML models cleanup result: {ml_cleanup_result}")
    except Exception as e:
        logger.warning(f"ML models cleanup failed: {e}")
    
    if force_delete and current_user.is_superuser:
        # Hard delete (only for superusers)
        db.delete(dataset)
        db.commit()
        return {
            "message": "Dataset permanently deleted",
            "dataset_id": dataset_id,
            "deletion_type": "hard"
        }
    else:
        # Soft delete
        dataset.soft_delete(current_user.id)
        db.commit()
        return {
            "message": "Dataset deleted successfully",
            "dataset_id": dataset_id,
            "deletion_type": "soft",
            "deleted_at": dataset.deleted_at
        }


@router.patch("/{dataset_id}/activate")
async def activate_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activate a dataset."""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.is_deleted == False
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or deleted"
        )
    
    # Check permissions
    data_service = DataSharingService(db)
    if not data_service.can_access_dataset(current_user, dataset) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this dataset"
        )
    
    dataset.activate()
    db.commit()
    
    return {
        "message": "Dataset activated successfully",
        "dataset_id": dataset_id,
        "status": dataset.status
    }


@router.patch("/{dataset_id}/deactivate")
async def deactivate_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate a dataset."""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.is_deleted == False
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or deleted"
        )
    
    # Check if user is owner or admin
    if dataset.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only deactivate your own datasets"
        )
    
    dataset.deactivate()
    db.commit()
    
    return {
        "message": "Dataset deactivated successfully",
        "dataset_id": dataset_id,
        "status": dataset.status
    }

@router.post("/upload")
async def upload_dataset_file(
    file: UploadFile = File(...),
    name: str = None,
    description: str = None,
    sharing_level: DataSharingLevel = DataSharingLevel.PRIVATE,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a dataset file."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must be part of an organization to upload datasets"
        )
    
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ['csv', 'json', 'xlsx', 'xls', 'txt', 'pdf']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Supported formats: CSV, JSON, Excel, TXT, PDF"
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Create dataset record first to get ID for storage
    dataset_name = name or file.filename.rsplit('.', 1)[0]
    
    # Create temporary dataset to get ID
    temp_dataset = Dataset(
        name=dataset_name,
        description=description,
        type=DatasetType.CSV,  # Temporary, will be updated
        status=DatasetStatus.PROCESSING,
        owner_id=current_user.id,
        organization_id=current_user.organization_id,
        department_id=current_user.department_id,
        sharing_level=sharing_level,
        size_bytes=file_size,
        allow_download=True,
        allow_api_access=True
    )
    
    db.add(temp_dataset)
    db.commit()
    db.refresh(temp_dataset)
    
    # Store file using storage service
    try:
        storage_result = await storage_service.store_dataset_file(
            file_content=content,
            original_filename=file.filename,
            dataset_id=temp_dataset.id,
            organization_id=current_user.organization_id
        )
        logger.info(f"✅ File stored successfully: {storage_result['filename']}")
    except Exception as e:
        # Clean up dataset record if storage fails
        db.delete(temp_dataset)
        db.commit()
        logger.error(f"❌ File storage failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store file: {str(e)}"
        )
    
    dataset_name = name or file.filename.rsplit('.', 1)[0]
    
    # Determine dataset type
    if file_extension == 'csv':
        dataset_type = DatasetType.CSV
    elif file_extension == 'json':
        dataset_type = DatasetType.JSON
    elif file_extension in ['xlsx', 'xls']:
        dataset_type = DatasetType.EXCEL
    elif file_extension == 'pdf':
        dataset_type = DatasetType.PDF
    else:
        dataset_type = DatasetType.CSV  # Default fallback
    
    # Process file content and extract metadata
    file_metadata = {}
    content_preview = None
    row_count = None
    column_count = None
    
    # Save file temporarily for processing
    import tempfile
    import os
    
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Process different file types
        if file_extension in ["pdf", "json"]:
            try:
                content_result = mindsdb_service.process_file_content(temp_file_path, file_extension)
                if content_result.get("success"):
                    file_metadata = content_result.get("metadata", {})
                    content_preview = content_result["content"][:500] + "..." if len(content_result["content"]) > 500 else content_result["content"]
                    
                    # Extract counts for metadata
                    if file_extension == "json":
                        row_count = file_metadata.get("element_count")
                        column_count = 1  # JSON treated as single complex column
                    
                    logger.info(f"Successfully processed {file_extension} file: {file_metadata}")
            except Exception as e:
                logger.warning(f"Could not process {file_extension} file content: {e}")
        
        # For CSV files, try to get basic info
        elif file_extension == "csv":
            try:
                import pandas as pd
                df = pd.read_csv(temp_file_path)
                file_metadata = {
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": df.columns.tolist(),
                    "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
                }
                content_preview = df.head(3).to_string()
                row_count = len(df)
                column_count = len(df.columns)
                logger.info(f"Successfully analyzed CSV file: {file_metadata}")
            except Exception as e:
                logger.warning(f"Could not analyze CSV file: {e}")
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    # Generate enhanced metadata for the new fields
    schema_metadata = {}
    quality_metrics = {}
    column_statistics = {}
    preview_data = {}
    
    if file_metadata:
        # Enhanced schema metadata
        schema_metadata = {
            "file_type": file_extension,
            "original_filename": file.filename,
            "encoding": "utf-8",  # Default assumption
            "structure": file_metadata.get("structure", {}),
            "columns": file_metadata.get("columns", []),
            "data_types": file_metadata.get("dtypes", {}),
            "sample_data": file_metadata.get("sample_data", [])
        }
        
        # Basic quality metrics
        quality_metrics = {
            "overall_score": 0.85,  # Default good score
            "completeness": 1.0 if row_count and row_count > 0 else 0.0,
            "consistency": 0.9,  # Default assumption
            "accuracy": 0.8,  # Default assumption
            "issues": [],
            "last_analyzed": datetime.utcnow().isoformat()
        }
        
        # Column statistics from file metadata
        if "column_stats" in file_metadata:
            column_statistics = file_metadata["column_stats"]
        elif "dtypes" in file_metadata:
            # Generate basic column stats
            column_statistics = {}
            for col, dtype in file_metadata["dtypes"].items():
                column_statistics[col] = {
                    "data_type": dtype,
                    "non_null_count": row_count or 0,
                    "null_count": 0,
                    "unique_count": "unknown"
                }
        
        # Preview data structure
        preview_data = {
            "headers": file_metadata.get("columns", []),
            "sample_rows": file_metadata.get("sample_data", [])[:10],  # First 10 rows
            "total_rows": row_count or 0,
            "is_sample": True,
            "preview_generated_at": datetime.utcnow().isoformat()
        }

    # Update the temporary dataset with complete information
    temp_dataset.name = dataset_name
    temp_dataset.description = description
    temp_dataset.type = dataset_type
    temp_dataset.status = DatasetStatus.ACTIVE
    temp_dataset.size_bytes = file_size
    temp_dataset.source_url = storage_result['relative_path']  # Storage service path
    temp_dataset.file_path = storage_result['file_path']  # Actual file storage path
    temp_dataset.row_count = row_count
    temp_dataset.column_count = column_count
    temp_dataset.file_metadata = file_metadata
    temp_dataset.content_preview = content_preview
    # New enhanced metadata fields
    temp_dataset.schema_metadata = schema_metadata
    temp_dataset.quality_metrics = quality_metrics
    temp_dataset.column_statistics = column_statistics
    temp_dataset.preview_data = preview_data
    temp_dataset.download_count = 0  # Initialize download count
    temp_dataset.last_downloaded_at = None
    
    # Use the updated dataset
    db_dataset = temp_dataset
    
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    
    # Automatically create ML models for this dataset
    ml_model_result = None
    try:
        logger.info(f"Creating ML models for dataset {db_dataset.id}: {dataset_name}")
        
        # Try to create the ML model with retry logic
        max_retries = 2
        for attempt in range(max_retries):
            try:
                ml_model_result = mindsdb_service.create_dataset_ml_model(
                    dataset_id=db_dataset.id,
                    dataset_name=dataset_name,
                    dataset_type=dataset_type.value,
                    dataset_content=content_preview
                )
                
                if ml_model_result.get("success"):
                    logger.info(f"ML models created successfully for dataset {db_dataset.id} on attempt {attempt + 1}")
                    break
                else:
                    logger.warning(f"ML model creation failed for dataset {db_dataset.id} on attempt {attempt + 1}: {ml_model_result.get('error')}")
                    if attempt == max_retries - 1:  # Last attempt
                        logger.error(f"All attempts failed for ML model creation for dataset {db_dataset.id}")
                    else:
                        time.sleep(2)  # Wait before retry
                        
            except Exception as e:
                logger.error(f"Exception during ML model creation attempt {attempt + 1} for dataset {db_dataset.id}: {e}")
                if attempt == max_retries - 1:  # Last attempt
                    ml_model_result = {
                        "success": False,
                        "error": str(e),
                        "message": "ML model creation failed after all retry attempts"
                    }
                else:
                    time.sleep(2)  # Wait before retry
            
    except Exception as e:
        logger.error(f"Error in ML model creation process for dataset {db_dataset.id}: {e}")
        ml_model_result = {
            "success": False,
            "error": str(e),
            "message": "ML model creation failed but dataset was uploaded successfully"
        }
    
    # Prepare comprehensive response
    response_data = {
        "message": "Dataset uploaded successfully",
        "dataset": db_dataset,
        "ml_models": ml_model_result
    }

    # Add helpful information about AI chat availability
    if ml_model_result and ml_model_result.get("success"):
        response_data["ai_chat_available"] = True
        response_data["chat_model_name"] = ml_model_result.get("chat_model")
        response_data["ai_features"] = {
            "chat_enabled": True,
            "model_ready": True,
            "chat_endpoint": f"/api/datasets/{db_dataset.id}/chat"
        }
    else:
        response_data["ai_chat_available"] = False
        response_data["ai_features"] = {
            "chat_enabled": False,
            "model_ready": False,
            "error": ml_model_result.get("error") if ml_model_result else "Unknown error",
            "retry_endpoint": f"/api/datasets/{db_dataset.id}/recreate-models"
        }
    
    return response_data

@router.get("/{dataset_id}/download")
async def download_dataset(
    dataset_id: int,
    file_format: str = "original",
    compression: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download a dataset file with secure token-based access."""
    from app.services.download import DownloadService
    
    download_service = DownloadService(db)
    
    # Initiate download and get secure token
    download_info = await download_service.initiate_download(
        dataset_id=dataset_id,
        user=current_user,
        file_format=file_format,
        compression=compression
    )
    
    return download_info

@router.get("/download/{download_token}")
async def execute_download(
    download_token: str,
    range: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Execute the actual file download using a secure token with resumable download support.
    
    The Range header can be used for resumable downloads (e.g., "bytes=1024-").
    """
    from app.services.download import DownloadService
    
    download_service = DownloadService(db)
    
    # Execute the download with range support for resumable downloads
    return await download_service.execute_download(
        download_token=download_token,
        use_streaming=True,
        range_header=range
    )

@router.get("/download/{download_token}/progress")
async def get_download_progress(
    download_token: str,
    db: Session = Depends(get_db)
):
    """
    Get download progress information.
    
    Returns detailed progress information including status, percentage, 
    transfer rate, and estimated time remaining.
    """
    from app.services.download import DownloadService
    
    download_service = DownloadService(db)
    
    return download_service.get_download_progress(download_token)

@router.post("/download/{download_token}/retry")
async def retry_download(
    download_token: str,
    db: Session = Depends(get_db)
):
    """
    Retry a failed or interrupted download.
    
    This endpoint allows resuming downloads that were interrupted due to network issues
    or retrying downloads that failed for other reasons.
    """
    from app.services.download import DownloadService
    
    download_service = DownloadService(db)
    download_info = download_service.get_download_progress(download_token)
    
    # Check if download can be retried
    if download_info["status"] not in ["failed", "interrupted", "expired"]:
        return {
            "message": "Download is already in progress or completed",
            "status": download_info["status"],
            "can_retry": False,
            "download_info": download_info
        }
    
    # Reset download status for retry
    download_record = db.query(DatasetDownload).filter(
        DatasetDownload.download_token == download_token
    ).first()
    
    if not download_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download not found"
        )
    
    # Update download record for retry
    download_record.download_status = "pending"
    download_record.error_message = None
    download_record.expires_at = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    
    return {
        "message": "Download ready for retry",
        "download_token": download_token,
        "status": "pending",
        "can_retry": True,
        "expires_at": download_record.expires_at.isoformat()
    }

@router.get("/{dataset_id}/download-history")
async def get_download_history(
    dataset_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get download history for a dataset (owner only)."""
    from app.services.download import DownloadService
    
    download_service = DownloadService(db)
    
    return download_service.get_download_history(
        dataset_id=dataset_id,
        user=current_user,
        limit=limit
    )

@router.get("/{dataset_id}/stats")
async def get_dataset_stats(
    dataset_id: int,
    include_downloads: bool = True,
    include_access_logs: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive statistics for a dataset."""
    data_service = DataSharingService(db)
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Check access permissions
    if not data_service.can_access_dataset(current_user, dataset):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this dataset"
        )
    
    try:
        stats_response = {
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "basic_stats": {
                "total_size_bytes": dataset.size_bytes,
                "row_count": dataset.row_count,
                "column_count": dataset.column_count,
                "file_type": dataset.type.value if dataset.type else "unknown",
                "sharing_level": dataset.sharing_level.value if dataset.sharing_level else "private",
                "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
                "updated_at": dataset.updated_at.isoformat() if dataset.updated_at else None,
                "last_accessed": dataset.last_accessed.isoformat() if dataset.last_accessed else None
            },
            "usage_stats": {
                "download_count": dataset.download_count or 0,
                "last_downloaded_at": dataset.last_downloaded_at.isoformat() if dataset.last_downloaded_at else None,
                "is_downloadable": dataset.allow_download,
                "api_access_enabled": dataset.allow_api_access,
                "ai_chat_enabled": dataset.allow_ai_chat
            }
        }
        
        # Include download statistics if requested and user is owner
        if include_downloads and (dataset.owner_id == current_user.id or current_user.is_superuser):
            from app.models.dataset import DatasetDownload
            
            # Get download statistics
            download_stats = db.query(DatasetDownload).filter(
                DatasetDownload.dataset_id == dataset_id
            ).all()
            
            successful_downloads = [d for d in download_stats if d.download_status == "completed"]
            failed_downloads = [d for d in download_stats if d.download_status == "failed"]
            
            stats_response["download_analytics"] = {
                "total_download_attempts": len(download_stats),
                "successful_downloads": len(successful_downloads),
                "failed_downloads": len(failed_downloads),
                "success_rate": len(successful_downloads) / len(download_stats) if download_stats else 0,
                "average_download_time": sum(d.download_duration_seconds or 0 for d in successful_downloads) / len(successful_downloads) if successful_downloads else 0,
                "popular_formats": {}
            }
            
            # Format popularity
            format_counts = {}
            for download in download_stats:
                format_counts[download.file_format] = format_counts.get(download.file_format, 0) + 1
            stats_response["download_analytics"]["popular_formats"] = format_counts
        
        # Include access logs if requested and user is owner
        if include_access_logs and (dataset.owner_id == current_user.id or current_user.is_superuser):
            from app.models.dataset import DatasetAccessLog
            
            recent_access = db.query(DatasetAccessLog).filter(
                DatasetAccessLog.dataset_id == dataset_id
            ).order_by(DatasetAccessLog.created_at.desc()).limit(10).all()
            
            stats_response["recent_access"] = [
                {
                    "access_type": log.access_type,
                    "user_id": log.user_id,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in recent_access
            ]
        
        # Include quality metrics if available
        if dataset.quality_metrics:
            stats_response["quality_summary"] = {
                "overall_score": dataset.quality_metrics.get("overall_score"),
                "completeness": dataset.quality_metrics.get("completeness"),
                "consistency": dataset.quality_metrics.get("consistency"),
                "accuracy": dataset.quality_metrics.get("accuracy"),
                "last_analyzed": dataset.quality_metrics.get("last_analyzed")
            }
        
        # Log access
        data_service.log_access(
            user=current_user,
            dataset=dataset,
            access_type="stats"
        )
        
        return stats_response
        
    except Exception as e:
        logger.error(f"❌ Failed to get stats for dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dataset statistics: {str(e)}"
        )

@router.post("/{dataset_id}/chat")
async def chat_with_dataset(
    dataset_id: int,
    message: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Chat with the AI model specifically trained for this dataset."""
    # Check if dataset exists and user has access
    data_service = DataSharingService(db)
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Check access permissions
    if not data_service.can_access_dataset(current_user, dataset):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this dataset"
        )
    
    # Extract message
    user_message = message.get("message", "")
    
    if not user_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message is required"
        )
    
    try:
        # Use dataset-specific chat with analytics
        response = mindsdb_service.chat_with_dataset(
            dataset_id=str(dataset_id),
            message=user_message,
            user_id=current_user.id,
            session_id=message.get("session_id"),
            organization_id=current_user.organization_id
        )
        
        # Log the interaction
        data_service.log_access(
            user=current_user,
            dataset=dataset,
            access_type="ai_chat"
        )
        
        return {
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "question": user_message,
            "model_type": "chat",
            **response
        }
        
    except Exception as e:
        logger.error(f"Dataset chat failed for dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat with dataset failed: {str(e)}"
        )

@router.get("/{dataset_id}/models")
async def get_dataset_models(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get information about ML models associated with this dataset."""
    # Check if dataset exists and user has access
    data_service = DataSharingService(db)
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Check access permissions
    if not data_service.can_access_dataset(current_user, dataset):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this dataset"
        )
    
    try:
        # Get model information from MindsDB
        models_info = []
        
        # Check chat model
        chat_model_name = f"dataset_{dataset_id}_chat_model"
        
        # Query MindsDB for model status
        try:
            models_query = f"SHOW MODELS WHERE name LIKE 'dataset_{dataset_id}_%';"
            result = mindsdb_service.execute_query(models_query)
            
            if result.get('data'):
                for model_data in result['data']:
                    model_info = {
                        "name": model_data[0] if len(model_data) > 0 else "unknown",
                        "engine": model_data[1] if len(model_data) > 1 else "unknown",
                        "status": model_data[5] if len(model_data) > 5 else "unknown",
                        "predict": model_data[7] if len(model_data) > 7 else "unknown",
                    }
                    models_info.append(model_info)
            
        except Exception as e:
            logger.warning(f"Could not fetch model status for dataset {dataset_id}: {e}")
        
        return {
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "models": models_info,
            "available_models": {
                "chat_model": chat_model_name
            },
            "endpoints": {
                "chat": f"/api/datasets/{dataset_id}/chat"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get model info for dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model information: {str(e)}"
        )

@router.post("/{dataset_id}/recreate-models")
async def recreate_dataset_models(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recreate ML models for this dataset (owner only)."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Only owner or superuser can recreate models
    if dataset.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only dataset owner can recreate models"
        )
    
    try:
        # First, clean up existing models
        logger.info(f"Recreating ML models for dataset {dataset_id}")
        cleanup_result = mindsdb_service.delete_dataset_models(dataset_id)
        
        # Create new models
        ml_model_result = mindsdb_service.create_dataset_ml_model(
            dataset_id=dataset_id,
            dataset_name=dataset.name,
            dataset_type=dataset.type.value
        )
        
        return {
            "message": "Dataset models recreated successfully",
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "cleanup_result": cleanup_result,
            "creation_result": ml_model_result
        }
        
    except Exception as e:
        logger.error(f"Failed to recreate models for dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recreate models: {str(e)}"
        )

# Enhanced Dataset Management API Endpoints

@router.get("/{dataset_id}/metadata")
async def get_dataset_metadata(
    dataset_id: int,
    refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed metadata for a dataset."""
    from app.services.cache import cache_service
    
    data_service = DataSharingService(db)
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Check access permissions
    if not data_service.can_access_dataset(current_user, dataset):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this dataset"
        )
    
    try:
        metadata_service = MetadataService(db)
        
        # Check cache first (unless refresh is requested)
        if not refresh:
            cached_metadata = cache_service.get(dataset_id, "metadata", ttl=3600)
            if cached_metadata:
                logger.info(f"📋 Returning cached metadata for dataset {dataset_id}")
                return cached_metadata["data"]
        
        # Generate fresh metadata
        logger.info(f"📋 Generating fresh metadata for dataset {dataset_id}")
        
        schema_metadata = await metadata_service.analyze_dataset_schema(dataset)
        quality_metrics = await metadata_service.get_data_quality_metrics(dataset)
        column_statistics = await metadata_service.generate_column_statistics(dataset)
        
        metadata_response = {
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "schema_metadata": schema_metadata,
            "quality_metrics": quality_metrics,
            "column_statistics": column_statistics,
            "basic_info": {
                "type": dataset.type.value if dataset.type else "unknown",
                "size_bytes": dataset.size_bytes,
                "row_count": dataset.row_count,
                "column_count": dataset.column_count,
                "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
                "updated_at": dataset.updated_at.isoformat() if dataset.updated_at else None
            },
            "generated_at": schema_metadata.get("analysis_timestamp")
        }
        
        # Cache the result
        cache_service.set(dataset_id, "metadata", metadata_response, ttl=3600)
        
        # Log access
        data_service.log_access(
            user=current_user,
            dataset=dataset,
            access_type="metadata"
        )
        
        return metadata_response
        
    except Exception as e:
        logger.error(f"❌ Failed to get metadata for dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metadata: {str(e)}"
        )

@router.get("/{dataset_id}/preview")
async def get_dataset_preview(
    dataset_id: int,
    rows: int = 20,
    include_stats: bool = True,
    refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dataset content preview."""
    from app.services.cache import cache_service
    
    data_service = DataSharingService(db)
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Check access permissions
    if not data_service.can_access_dataset(current_user, dataset):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this dataset"
        )
    
    try:
        preview_service = PreviewService(db)
        
        # Check cache first (unless refresh is requested)
        cache_key_params = {"rows": rows, "include_stats": include_stats}
        if not refresh:
            cached_preview = cache_service.get(dataset_id, "preview", ttl=1800, **cache_key_params)
            if cached_preview:
                logger.info(f"👁️ Returning cached preview for dataset {dataset_id}")
                return cached_preview["data"]
        
        # Generate fresh preview
        logger.info(f"👁️ Generating fresh preview for dataset {dataset_id}")
        
        preview_data = await preview_service.generate_preview_data(
            dataset=dataset,
            rows=rows,
            include_stats=include_stats
        )
        
        preview_response = {
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "preview": preview_data,
            "request_params": {
                "rows_requested": rows,
                "include_stats": include_stats
            }
        }
        
        # Cache the result
        cache_service.set(dataset_id, "preview", preview_response, ttl=1800, **cache_key_params)
        
        # Log access
        data_service.log_access(
            user=current_user,
            dataset=dataset,
            access_type="preview"
        )
        
        return preview_response
        
    except Exception as e:
        logger.error(f"❌ Failed to get preview for dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preview: {str(e)}"
        )

@router.post("/{dataset_id}/download-token")
async def generate_download_token(
    dataset_id: int,
    file_format: str = "original",
    compression: Optional[str] = None,
    expires_in_hours: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a secure download token for dataset access."""
    from app.services.download import DownloadService
    
    download_service = DownloadService(db)
    
    # Generate download token with custom expiration
    download_info = await download_service.initiate_download(
        dataset_id=dataset_id,
        user=current_user,
        file_format=file_format,
        compression=compression
    )
    
    return {
        "message": "Download token generated successfully",
        "download_token": download_info["download_token"],
        "expires_at": download_info["expires_at"],
        "dataset_id": dataset_id,
        "file_format": file_format,
        "compression": compression
    }

@router.post("/{dataset_id}/refresh-metadata")
async def refresh_dataset_metadata(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Refresh and update dataset metadata (owner only)."""
    from app.services.cache import cache_service
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Only owner or superuser can refresh metadata
    if dataset.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only dataset owner can refresh metadata"
        )
    
    try:
        metadata_service = MetadataService(db)
        
        # Update metadata in database
        result = await metadata_service.update_dataset_metadata(dataset_id)
        
        # Clear cache
        cache_service.clear_dataset_cache(dataset_id)
        
        logger.info(f"🔄 Metadata refreshed for dataset {dataset_id}")
        
        return {
            "message": "Dataset metadata refreshed successfully",
            "dataset_id": dataset_id,
            "status": result.get("status"),
            "updated_at": result.get("updated_at")
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to refresh metadata for dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh metadata: {str(e)}"
        )

@router.get("/{dataset_id}/schema")
async def get_dataset_schema(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dataset schema information."""
    data_service = DataSharingService(db)
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Check access permissions
    if not data_service.can_access_dataset(current_user, dataset):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this dataset"
        )
    
    try:
        # Return schema from cached metadata or database
        schema_info = dataset.schema_metadata or dataset.schema_info or {}
        
        schema_response = {
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "schema": schema_info,
            "basic_info": {
                "type": dataset.type.value if dataset.type else "unknown",
                "row_count": dataset.row_count,
                "column_count": dataset.column_count
            }
        }
        
        # Log access
        data_service.log_access(
            user=current_user,
            dataset=dataset,
            access_type="schema"
        )
        
        return schema_response
        
    except Exception as e:
        logger.error(f"❌ Failed to get schema for dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schema: {str(e)}"
        )

@router.post("/{dataset_id}/transfer-ownership")
async def transfer_dataset_ownership(
    dataset_id: int,
    new_owner_id: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Transfer ownership of a dataset to another user within the same organization."""
    from app.models.user import User
    
    # Get the dataset
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Check if current user is the owner or admin
    if dataset.owner_id != current_user.id and not current_user.is_superuser:
        # Check if user is organization admin
        if not (current_user.organization_id == dataset.organization_id and 
                current_user.role in ["owner", "admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only dataset owner or organization admin can transfer ownership"
            )
    
    # Get the new owner
    new_owner = db.query(User).filter(User.id == new_owner_id).first()
    if not new_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="New owner user not found"
        )
    
    # Check if new owner is in the same organization
    if new_owner.organization_id != dataset.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New owner must be in the same organization as the dataset"
        )
    
    # Check if new owner is different from current owner
    if new_owner_id == dataset.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset is already owned by this user"
        )
    
    try:
        # Store old owner info for logging
        old_owner_id = dataset.owner_id
        
        # Transfer ownership
        dataset.owner_id = new_owner_id
        dataset.updated_at = datetime.utcnow()
        
        # Log the ownership transfer
        from app.models.dataset import DatasetAccessLog
        access_log = DatasetAccessLog(
            dataset_id=dataset_id,
            user_id=current_user.id,
            access_type="ownership_transfer",
            ip_address=None,
            user_agent=None,
            details={
                "old_owner_id": old_owner_id,
                "new_owner_id": new_owner_id,
                "transferred_by": current_user.id
            }
        )
        db.add(access_log)
        
        db.commit()
        db.refresh(dataset)
        
        logger.info(f"📋 Dataset {dataset_id} ownership transferred from user {old_owner_id} to user {new_owner_id} by user {current_user.id}")
        
        return {
            "message": "Dataset ownership transferred successfully",
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "old_owner_id": old_owner_id,
            "new_owner_id": new_owner_id,
            "transferred_by": current_user.id,
            "transferred_at": dataset.updated_at.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to transfer ownership for dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to transfer ownership: {str(e)}"
        )