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

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[DatasetResponse])
async def get_datasets(
    skip: int = 0,
    limit: int = 100,
    sharing_level: Optional[DataSharingLevel] = None,
    dataset_type: Optional[DatasetType] = None,
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
        sharing_level=sharing_level
    )
    
    return datasets

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a dataset (only owner can delete)."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Only owner or superuser can delete
    if dataset.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only dataset owner can delete"
        )
    
    # Clean up ML models before deleting dataset
    ml_cleanup_result = None
    try:
        logger.info(f"Cleaning up ML models for dataset {dataset_id}")
        ml_cleanup_result = mindsdb_service.delete_dataset_models(dataset_id)
        
        if ml_cleanup_result.get("success"):
            logger.info(f"ML models cleaned up successfully for dataset {dataset_id}")
        else:
            logger.warning(f"ML model cleanup failed for dataset {dataset_id}: {ml_cleanup_result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error cleaning up ML models for dataset {dataset_id}: {e}")
        ml_cleanup_result = {
            "success": False,
            "error": str(e),
            "message": "ML model cleanup failed but dataset will still be deleted"
        }
    
    db.delete(dataset)
    db.commit()
    
    return {
        "message": "Dataset deleted successfully",
        "ml_cleanup": ml_cleanup_result
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
    
    # Create dataset record
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
        allow_api_access=True
    )
    
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    
    # Automatically create ML models for this dataset
    ml_model_result = None
    try:
        logger.info(f"Creating ML models for dataset {db_dataset.id}: {dataset_name}")
        ml_model_result = mindsdb_service.create_dataset_ml_model(
            dataset_id=db_dataset.id,
            dataset_name=dataset_name,
            dataset_type=dataset_type.value,
            user_id=current_user.id
        )
        
        if ml_model_result.get("success"):
            logger.info(f"ML models created successfully for dataset {db_dataset.id}")
        else:
            logger.warning(f"ML model creation failed for dataset {db_dataset.id}: {ml_model_result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error creating ML models for dataset {db_dataset.id}: {e}")
        ml_model_result = {
            "success": False,
            "error": str(e),
            "message": "ML model creation failed but dataset was uploaded successfully"
        }
    
    return {
        "message": "Dataset uploaded successfully",
        "dataset": db_dataset,
        "ml_models": ml_model_result
    }

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
        # Use dataset-specific chat
        response = mindsdb_service.chat_with_dataset(
            dataset_id=dataset_id,
            message=user_message,
            model_type="chat"
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
            dataset_type=dataset.type.value,
            user_id=current_user.id
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