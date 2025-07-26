from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.auth import get_current_superuser
from app.models.user import User
from app.models.config import Configuration
from app.models.dataset import Dataset
from app.models.analytics import DatasetAccess, SystemMetrics, AccessRequest, AuditLog
from app.schemas.config import Configuration as ConfigSchema, ConfigurationCreate, ConfigurationUpdate
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/config", response_model=List[ConfigSchema])
async def get_configurations(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Get all configuration settings."""
    configs = db.query(Configuration).all()
    return configs


@router.post("/config", response_model=ConfigSchema)
async def create_configuration(
    config: ConfigurationCreate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Create a new configuration setting."""
    # Check if configuration already exists
    existing_config = db.query(Configuration).filter(Configuration.key == config.key).first()
    if existing_config:
        raise HTTPException(status_code=400, detail="Configuration key already exists")
    
    db_config = Configuration(**config.dict())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.put("/config/{config_key}", response_model=ConfigSchema)
async def update_configuration(
    config_key: str,
    config_update: ConfigurationUpdate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Update a configuration setting."""
    config = db.query(Configuration).filter(Configuration.key == config_key).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    update_data = config_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    return config


@router.delete("/config/{config_key}")
async def delete_configuration(
    config_key: str,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Delete a configuration setting."""
    config = db.query(Configuration).filter(Configuration.key == config_key).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    db.delete(config)
    db.commit()
    return {"message": "Configuration deleted successfully"}


@router.get("/config/{config_key}", response_model=ConfigSchema)
async def get_configuration(
    config_key: str,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Get a specific configuration setting."""
    config = db.query(Configuration).filter(Configuration.key == config_key).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config


@router.post("/google-api-key")
async def set_google_api_key(
    api_key_data: Dict[str, str],
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Set or update Google API key."""
    api_key = api_key_data.get("api_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    # Check if configuration exists
    config = db.query(Configuration).filter(Configuration.key == "google_api_key").first()
    
    if config:
        config.value = api_key
    else:
        config = Configuration(
            key="google_api_key",
            value=api_key,
            description="Google API key for Gemini Flash integration"
        )
        db.add(config)
    
    db.commit()
    return {"message": "Google API key updated successfully"}


@router.get("/google-api-key")
async def get_google_api_key(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Get Google API key status."""
    config = db.query(Configuration).filter(Configuration.key == "google_api_key").first()
    
    return {
        "has_api_key": config is not None and config.value is not None,
        "key_length": len(config.value) if config and config.value else 0
    }


@router.get("/stats")
async def get_admin_stats(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics."""
    try:
        # Get date ranges
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Total users
        total_users = db.query(User).count()
        
        # Active users (users who accessed data in last 7 days)
        active_users = db.query(func.count(func.distinct(DatasetAccess.user_id))).filter(
            DatasetAccess.timestamp >= last_7d
        ).scalar() or 0
        
        # Total datasets (only active, non-deleted)
        active_datasets_count = db.query(Dataset).filter(
            Dataset.is_deleted == False,
            Dataset.is_active == True
        ).count()
        
        # Pending requests
        pending_requests = db.query(func.count(AccessRequest.id)).filter(AccessRequest.status == 'pending').scalar() or 0
        
        # Get latest system metrics
        latest_metrics = db.query(SystemMetrics).order_by(
            SystemMetrics.timestamp.desc()
        ).first()
        
        # System health data
        system_health = {
            "uptime": "99.9%",  # Mock - would calculate from system start time
            "cpuUsage": latest_metrics.cpu_usage_percent if latest_metrics else 45,
            "memoryUsage": latest_metrics.memory_usage_percent if latest_metrics else 67,
            "diskUsage": latest_metrics.disk_usage_percent if latest_metrics else 78,
            "networkStatus": "healthy" if latest_metrics and latest_metrics.network_latency_ms < 200 else "warning"
        }
        
        # Recent activity (last 10 audit logs)
        recent_logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
        
        recent_activity = []
        for log in recent_logs:
            recent_activity.append({
                "id": str(log.id),
                "type": log.action,
                "description": log.details,
                "timestamp": log.timestamp.isoformat() + "Z",
                "severity": "info"
            })
        
        return {
            "totalUsers": total_users,
            "activeUsers": active_users,
            "totalDatasets": active_datasets_count,
            "pendingRequests": pending_requests,
            "systemHealth": system_health,
            "recentActivity": recent_activity
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting admin stats: {str(e)}")


@router.get("/datasets")
async def get_admin_datasets(
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    include_inactive: bool = False,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Get all datasets for admin management with explicit control over deleted/inactive datasets."""
    logger.info(f"get_admin_datasets called by admin user {current_user.id} ({current_user.email})")
    logger.info(f"Admin parameters: skip={skip}, limit={limit}, include_deleted={include_deleted}, include_inactive={include_inactive}, organization_id={organization_id}")
    
    try:
        query = db.query(Dataset)
        
        # Filter by organization if specified
        if organization_id:
            query = query.filter(Dataset.organization_id == organization_id)
            logger.info(f"Filtered by organization_id: {organization_id}")
        
        # Filter deleted datasets unless explicitly requested
        if not include_deleted:
            query = query.filter(Dataset.is_deleted == False)
            logger.info("Filtered out deleted datasets")
        
        # Filter inactive datasets unless explicitly requested  
        if not include_inactive:
            query = query.filter(Dataset.is_active == True)
            logger.info("Filtered out inactive datasets")
        
        # Get total count before pagination
        total_count = query.count()
        logger.info(f"Total datasets matching criteria: {total_count}")
        
        # Apply pagination
        datasets = query.offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(datasets)} datasets after pagination")
        
        # Convert to response format
        dataset_responses = []
        for dataset in datasets:
            dataset_responses.append({
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "type": dataset.type,
                "sharing_level": dataset.sharing_level,
                "organization_id": dataset.organization_id,
                "owner_id": dataset.owner_id,
                "is_active": dataset.is_active,
                "is_deleted": dataset.is_deleted,
                "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
                "updated_at": dataset.updated_at.isoformat() if dataset.updated_at else None,
                "deleted_at": dataset.deleted_at.isoformat() if dataset.deleted_at else None,
                "deleted_by": dataset.deleted_by,
                "size_bytes": dataset.size_bytes,
                "allow_download": dataset.allow_download,
                "allow_api_access": dataset.allow_api_access
            })
        
        logger.info(f"Admin datasets endpoint returning {len(dataset_responses)} datasets")
        
        return {
            "datasets": dataset_responses,
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "filters": {
                "include_deleted": include_deleted,
                "include_inactive": include_inactive,
                "organization_id": organization_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_admin_datasets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving admin datasets: {str(e)}")


@router.delete("/datasets/{dataset_id}")
async def admin_delete_dataset(
    dataset_id: int,
    force_delete: bool = False,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Admin endpoint to delete datasets with optional force delete."""
    try:
        # Find dataset (including deleted ones for admin)
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        
        if not dataset:
            raise HTTPException(
                status_code=404,
                detail="Dataset not found"
            )
        
        if dataset.is_deleted and not force_delete:
            raise HTTPException(
                status_code=400,
                detail="Dataset is already deleted. Use force_delete=true to permanently delete."
            )
        
        # Clean up associated ML models first
        try:
            from app.services.mindsdb import MindsDBService
            mindsdb_service = MindsDBService()
            ml_cleanup_result = mindsdb_service.delete_dataset_models(dataset_id)
            logger.info(f"ML models cleanup result: {ml_cleanup_result}")
        except Exception as e:
            logger.warning(f"ML models cleanup failed: {e}")
        
        if force_delete:
            # Hard delete (permanent removal)
            db.delete(dataset)
            db.commit()
            return {
                "message": "Dataset permanently deleted",
                "dataset_id": dataset_id,
                "deletion_type": "hard",
                "deleted_by": current_user.id
            }
        else:
            # Soft delete
            if not dataset.is_deleted:
                dataset.soft_delete(current_user.id)
                db.commit()
            return {
                "message": "Dataset deleted successfully",
                "dataset_id": dataset_id,
                "deletion_type": "soft",
                "deleted_at": dataset.deleted_at.isoformat() if dataset.deleted_at else None,
                "deleted_by": dataset.deleted_by
            }
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting dataset: {str(e)}")


@router.patch("/datasets/{dataset_id}/restore")
async def admin_restore_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Admin endpoint to restore a soft-deleted dataset."""
    try:
        # Find deleted dataset
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.is_deleted == True
        ).first()
        
        if not dataset:
            raise HTTPException(
                status_code=404,
                detail="Deleted dataset not found"
            )
        
        # Restore dataset
        dataset.is_deleted = False
        dataset.deleted_at = None
        dataset.deleted_by = None
        dataset.is_active = True
        dataset.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": "Dataset restored successfully",
            "dataset_id": dataset_id,
            "restored_by": current_user.id,
            "restored_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error restoring dataset: {str(e)}")


@router.get("/datasets/stats")
async def get_admin_dataset_stats(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Get comprehensive dataset statistics for admin dashboard."""
    try:
        # Total datasets (including deleted)
        total_datasets = db.query(Dataset).count()
        
        # Active datasets
        active_datasets = db.query(Dataset).filter(
            Dataset.is_deleted == False,
            Dataset.is_active == True
        ).count()
        
        # Deleted datasets
        deleted_datasets = db.query(Dataset).filter(Dataset.is_deleted == True).count()
        
        # Inactive datasets (not deleted but inactive)
        inactive_datasets = db.query(Dataset).filter(
            Dataset.is_deleted == False,
            Dataset.is_active == False
        ).count()
        
        # Datasets by sharing level
        sharing_stats = {}
        for level in ["PRIVATE", "ORGANIZATION", "PUBLIC"]:
            count = db.query(Dataset).filter(
                Dataset.is_deleted == False,
                Dataset.sharing_level == level
            ).count()
            sharing_stats[level.lower()] = count
        
        # Recent deletions (last 7 days)
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_deletions = db.query(Dataset).filter(
            Dataset.is_deleted == True,
            Dataset.deleted_at >= week_ago
        ).count()
        
        return {
            "total_datasets": total_datasets,
            "active_datasets": active_datasets,
            "deleted_datasets": deleted_datasets,
            "inactive_datasets": inactive_datasets,
            "recent_deletions": recent_deletions,
            "sharing_level_stats": sharing_stats,
            "health_status": {
                "deletion_rate": recent_deletions / max(total_datasets, 1) * 100,
                "active_rate": active_datasets / max(total_datasets, 1) * 100
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dataset stats: {str(e)}")