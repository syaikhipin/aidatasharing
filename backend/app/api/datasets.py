from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
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
import json
import logging
import time

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
        row_count=dataset_data.get("row_count"),
        column_count=len(dataset_data.get("columns", []))
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
    
    # TODO: Save file to storage (S3, local filesystem, etc.)
    # For now, we'll just create the dataset record
    
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

    # Create dataset record with enhanced metadata
    db_dataset = Dataset(
        name=dataset_name,
        description=description,
        type=dataset_type,
        status=DatasetStatus.ACTIVE,
        owner_id=current_user.id,
        organization_id=current_user.organization_id,
        department_id=current_user.department_id,
        sharing_level=sharing_level,
        size_bytes=file_size,
        source_url=f"uploads/{file.filename}",  # This would be actual storage path
        allow_download=True,
        allow_api_access=True,
        row_count=row_count,
        column_count=column_count,
        file_metadata=file_metadata,
        content_preview=content_preview
    )
    
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download a dataset file."""
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
    
    if not dataset.allow_download:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Downloads not allowed for this dataset"
        )
    
    # Log download
    data_service.log_access(
        user=current_user,
        dataset=dataset,
        access_type="download"
    )
    
    # TODO: Return actual file download
    # For now, return download URL
    return {
        "download_url": f"/files/{dataset.source_url}",
        "filename": f"{dataset.name}.{dataset.type}",
        "size_bytes": dataset.size_bytes
    }

@router.get("/{dataset_id}/stats")
async def get_dataset_stats(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a dataset."""
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
    
    # Get access logs for this dataset
    access_logs = []  # TODO: Implement access logs retrieval
    
    return {
        "dataset_id": dataset_id,
        "total_size": dataset.size_bytes,
        "row_count": dataset.row_count,
        "column_count": dataset.column_count,
        "recent_access": access_logs,
        "sharing_level": dataset.sharing_level,
        "created_at": dataset.created_at,
        "last_accessed": dataset.last_accessed
    }

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