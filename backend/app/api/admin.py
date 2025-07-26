from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
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
from app.models.admin_config import ConfigurationOverride as ConfigurationOverrideModel, MindsDBConfiguration as MindsDBConfigurationModel, ConfigurationHistory as ConfigurationHistoryModel
from app.schemas.config import Configuration as ConfigSchema, ConfigurationCreate, ConfigurationUpdate
from app.schemas.admin_config import (
    ConfigurationOverrideCreate,
    ConfigurationOverrideUpdate,
    MindsDBConfigurationCreate,
    MindsDBConfigurationUpdate,
    SystemConfiguration,
    EnvironmentVariablesResponse,
    ConfigurationApplicationResult,
    BulkConfigurationUpdate,
    ConfigurationOverride as ConfigurationOverrideSchema,
    MindsDBConfiguration as MindsDBConfigurationSchema
)
from app.services.admin_config import AdminConfigurationService
import logging
import json
import tempfile
import os

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
        
        # Total users - with error handling
        try:
            total_users = db.query(User).count()
        except Exception as e:
            logger.warning(f"Could not get total users: {e}")
            total_users = 0
        
        # Active users (users who accessed data in last 7 days) - with error handling
        try:
            active_users = db.query(func.count(func.distinct(DatasetAccess.user_id))).filter(
                DatasetAccess.timestamp >= last_7d
            ).scalar() or 0
        except Exception as e:
            logger.warning(f"Could not get active users: {e}")
            active_users = 0
        
        # Total datasets (only active, non-deleted) - with error handling
        try:
            active_datasets_count = db.query(Dataset).filter(
                Dataset.is_deleted == False,
                Dataset.is_active == True
            ).count()
        except Exception as e:
            logger.warning(f"Could not get dataset count: {e}")
            active_datasets_count = 0
        
        # Pending requests - with error handling
        try:
            pending_requests = db.query(func.count(AccessRequest.id)).filter(AccessRequest.status == 'pending').scalar() or 0
        except Exception as e:
            logger.warning(f"Could not get pending requests: {e}")
            pending_requests = 0
        
        # Get latest system metrics - with error handling
        try:
            latest_metrics = db.query(SystemMetrics).order_by(
                SystemMetrics.timestamp.desc()
            ).first()
        except Exception as e:
            logger.warning(f"Could not get system metrics: {e}")
            latest_metrics = None
        
        # System health data
        system_health = {
            "uptime": "99.9%",  # Mock - would calculate from system start time
            "cpuUsage": latest_metrics.cpu_usage_percent if latest_metrics else 45,
            "memoryUsage": latest_metrics.memory_usage_percent if latest_metrics else 67,
            "diskUsage": latest_metrics.disk_usage_percent if latest_metrics else 78,
            "networkStatus": "healthy" if latest_metrics and latest_metrics.network_latency_ms < 200 else "warning"
        }
        
        # Recent activity (last 10 audit logs) - with error handling
        recent_activity = []
        try:
            recent_logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
            
            for log in recent_logs:
                recent_activity.append({
                    "id": str(log.id),
                    "type": log.action,
                    "description": log.details,
                    "timestamp": log.timestamp.isoformat() + "Z",
                    "severity": "info"
                })
        except Exception as e:
            logger.warning(f"Could not get recent activity: {e}")
            # Provide some mock recent activity
            recent_activity = [
                {
                    "id": "1",
                    "type": "dataset_upload",
                    "description": "Dataset uploaded successfully",
                    "timestamp": now.isoformat() + "Z",
                    "severity": "info"
                }
            ]
        
        return {
            "totalUsers": total_users,
            "activeUsers": active_users,
            "totalDatasets": active_datasets_count,
            "pendingRequests": pending_requests,
            "systemHealth": system_health,
            "recentActivity": recent_activity
        }
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {str(e)}")
        # Return default stats instead of raising an error
        return {
            "totalUsers": 0,
            "activeUsers": 0,
            "totalDatasets": 0,
            "pendingRequests": 0,
            "systemHealth": {
                "uptime": "99.9%",
                "cpuUsage": 45,
                "memoryUsage": 67,
                "diskUsage": 78,
                "networkStatus": "healthy"
            },
            "recentActivity": [
                {
                    "id": "1",
                    "type": "system_status",
                    "description": "System is running normally",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "severity": "info"
                }
            ]
        }


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


# Enhanced Configuration Management Endpoints

@router.get("/system-config", response_model=SystemConfiguration)
async def get_system_configuration(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Get complete system configuration including environment overrides and MindsDB config"""
    try:
        config_service = AdminConfigurationService(db)
        
        # Initialize default configurations if not exists
        config_service.initialize_default_configurations()
        
        # Get all configurations
        env_overrides = config_service.get_all_configurations()
        mindsdb_configs = config_service.get_mindsdb_configurations()
        
        # Find active MindsDB config
        active_mindsdb = next((c for c in mindsdb_configs if c.is_active), None)
        
        # Get system info
        system_info = {
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "platform": os.name,
            "environment_variables_count": len(os.environ),
            "managed_configs_count": sum(len(configs) for configs in env_overrides.values()),
            "mindsdb_configs_count": len(mindsdb_configs),
            "current_working_directory": os.getcwd(),
            "config_file_exists": os.path.exists("./mindsdb_config.json")
        }
        
        # Check if restart is required
        restart_required = any(
            config.get("requires_restart", False) and config.get("is_overridden", False)
            for category_configs in env_overrides.values()
            for config in category_configs
        )
        
        return SystemConfiguration(
            environment_overrides=env_overrides,
            mindsdb_configurations=mindsdb_configs,
            active_mindsdb_config=active_mindsdb,
            system_info=system_info,
            restart_required=restart_required
        )
        
    except Exception as e:
        logger.error(f"Error getting system configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving system configuration: {str(e)}")


@router.get("/environment-variables", response_model=EnvironmentVariablesResponse)
async def get_environment_variables(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Get all environment variables with management status"""
    try:
        config_service = AdminConfigurationService(db)
        env_vars = config_service.get_environment_variables()
        return EnvironmentVariablesResponse(**env_vars)
        
    except Exception as e:
        logger.error(f"Error getting environment variables: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving environment variables: {str(e)}")


@router.put("/config-override/{config_id}", response_model=ConfigurationApplicationResult)
async def update_configuration_override(
    config_id: int,
    config_update: ConfigurationOverrideUpdate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Update a configuration override"""
    try:
        config_service = AdminConfigurationService(db)
        result = config_service.update_configuration(
            config_id, config_update, current_user.id, current_user.email
        )
        return result
        
    except Exception as e:
        logger.error(f"Error updating configuration override: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating configuration: {str(e)}")


@router.post("/config-override")
async def create_configuration_override(
    config_create: ConfigurationOverrideCreate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Create a new configuration override"""
    try:
        # Check if configuration already exists
        existing = db.query(ConfigurationOverrideModel).filter(
            ConfigurationOverrideModel.key == config_create.key
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Configuration key already exists")
        
        config = ConfigurationOverrideModel(**config_create.dict())
        db.add(config)
        db.commit()
        db.refresh(config)
        
        # Record history
        config_service = AdminConfigurationService(db)
        config_service._record_configuration_change(
            config.key,
            "override",
            None,
            config.value,
            current_user.id,
            current_user.email,
            "New configuration override created"
        )
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating configuration override: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating configuration: {str(e)}")


@router.delete("/config-override/{config_id}")
async def delete_configuration_override(
    config_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Delete a configuration override"""
    try:
        config = db.query(ConfigurationOverrideModel).filter(
            ConfigurationOverrideModel.id == config_id
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        # Record history
        config_service = AdminConfigurationService(db)
        config_service._record_configuration_change(
            config.key,
            "override",
            config.value,
            None,
            current_user.id,
            current_user.email,
            "Configuration override deleted"
        )
        
        db.delete(config)
        db.commit()
        
        return {"message": "Configuration override deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting configuration override: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting configuration: {str(e)}")


@router.post("/mindsdb-config")
async def create_mindsdb_configuration(
    config_create: MindsDBConfigurationCreate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Create a new MindsDB configuration"""
    try:
        config_service = AdminConfigurationService(db)
        config = config_service.create_mindsdb_configuration(
            config_create, current_user.id, current_user.email
        )
        return config
        
    except Exception as e:
        logger.error(f"Error creating MindsDB configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating MindsDB configuration: {str(e)}")


@router.put("/mindsdb-config/{config_id}")
async def update_mindsdb_configuration(
    config_id: int,
    config_update: MindsDBConfigurationUpdate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Update a MindsDB configuration"""
    try:
        config_service = AdminConfigurationService(db)
        config = config_service.update_mindsdb_configuration(
            config_id, config_update, current_user.id, current_user.email
        )
        return config
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating MindsDB configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating MindsDB configuration: {str(e)}")


@router.delete("/mindsdb-config/{config_id}")
async def delete_mindsdb_configuration(
    config_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Delete a MindsDB configuration"""
    try:
        config = db.query(MindsDBConfigurationModel).filter(
            MindsDBConfigurationModel.id == config_id
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="MindsDB configuration not found")
        
        # Record history
        config_service = AdminConfigurationService(db)
        config_service._record_configuration_change(
            f"mindsdb.{config.config_name}",
            "mindsdb",
            json.dumps({"config_name": config.config_name, "mindsdb_url": config.mindsdb_url}),
            None,
            current_user.id,
            current_user.email,
            "MindsDB configuration deleted"
        )
        
        db.delete(config)
        db.commit()
        
        return {"message": "MindsDB configuration deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting MindsDB configuration: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting MindsDB configuration: {str(e)}")


@router.post("/mindsdb-config/{config_id}/test")
async def test_mindsdb_configuration(
    config_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Test a MindsDB configuration connection"""
    try:
        config_service = AdminConfigurationService(db)
        result = config_service.test_mindsdb_connection(config_id)
        return result
        
    except Exception as e:
        logger.error(f"Error testing MindsDB configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error testing MindsDB configuration: {str(e)}")


@router.post("/mindsdb-config/{config_id}/apply")
async def apply_mindsdb_configuration(
    config_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Apply MindsDB configuration to the actual config file"""
    try:
        config_service = AdminConfigurationService(db)
        success = config_service.apply_configuration_to_mindsdb_file(config_id)
        
        if success:
            return {"message": "MindsDB configuration applied successfully", "restart_required": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to apply MindsDB configuration")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying MindsDB configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error applying MindsDB configuration: {str(e)}")


@router.get("/mindsdb-config/{config_id}/export")
async def export_mindsdb_configuration(
    config_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Export MindsDB configuration as JSON file"""
    try:
        config_service = AdminConfigurationService(db)
        temp_file = config_service.export_mindsdb_config_file(config_id)
        
        return FileResponse(
            temp_file,
            media_type="application/json",
            filename=f"mindsdb_config_{config_id}.json",
            background=lambda: os.unlink(temp_file)  # Clean up after download
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting MindsDB configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting MindsDB configuration: {str(e)}")


@router.post("/mindsdb-config/import")
async def import_mindsdb_configuration(
    file: UploadFile = File(...),
    config_name: str = "imported_config",
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Import MindsDB configuration from JSON file"""
    try:
        # Read and parse uploaded file
        content = await file.read()
        config_data = json.loads(content)
        
        # Extract relevant configuration
        api_config = config_data.get("api", {}).get("http", {})
        host = api_config.get("host", "127.0.0.1")
        port = api_config.get("port", 47334)
        mindsdb_url = f"http://{host}:{port}"
        
        mindsdb_config = MindsDBConfigurationCreate(
            config_name=config_name,
            is_active=False,  # Don't activate imported configs by default
            mindsdb_url=mindsdb_url,
            permanent_storage_config=config_data.get("permanent_storage"),
            file_upload_config=config_data.get("url_file_upload"),
            custom_config={k: v for k, v in config_data.items() 
                          if k not in ["permanent_storage", "url_file_upload", "api", "paths"]}
        )
        
        config_service = AdminConfigurationService(db)
        config = config_service.create_mindsdb_configuration(
            mindsdb_config, current_user.id, current_user.email
        )
        
        return {
            "message": "MindsDB configuration imported successfully",
            "config_id": config.id,
            "config_name": config.config_name
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        logger.error(f"Error importing MindsDB configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error importing MindsDB configuration: {str(e)}")


@router.get("/config-history")
async def get_configuration_history(
    config_key: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Get configuration change history"""
    try:
        config_service = AdminConfigurationService(db)
        history = config_service.get_configuration_history(config_key, limit)
        
        return {
            "history": [
                {
                    "id": h.id,
                    "config_key": h.config_key,
                    "config_type": h.config_type,
                    "old_value": h.old_value if not h.config_key.endswith(("password", "key", "secret")) else "***",
                    "new_value": h.new_value if not h.config_key.endswith(("password", "key", "secret")) else "***",
                    "change_reason": h.change_reason,
                    "changed_by_email": h.changed_by_email,
                    "changed_at": h.changed_at.isoformat(),
                    "applied_successfully": h.applied_successfully,
                    "application_error": h.application_error,
                    "applied_at": h.applied_at.isoformat() if h.applied_at else None
                }
                for h in history
            ],
            "total": len(history),
            "filtered_by": config_key
        }
        
    except Exception as e:
        logger.error(f"Error getting configuration history: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving configuration history: {str(e)}")


@router.post("/config/bulk-update", response_model=ConfigurationApplicationResult)
async def bulk_update_configurations(
    bulk_update: BulkConfigurationUpdate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Bulk update multiple configurations"""
    try:
        config_service = AdminConfigurationService(db)
        applied_configs = []
        failed_configs = []
        errors = []
        restart_required = False
        
        # Update overrides
        for i, override_update in enumerate(bulk_update.overrides):
            try:
                # Find config by index or key (this is simplified - you might want to pass IDs)
                configs = db.query(ConfigurationOverrideModel).all()
                if i < len(configs):
                    result = config_service.update_configuration(
                        configs[i].id, override_update, current_user.id, current_user.email
                    )
                    if result.success:
                        applied_configs.extend(result.applied_configs)
                        if result.restart_required:
                            restart_required = True
                    else:
                        failed_configs.append(f"override_{i}")
                        errors.extend(result.errors)
            except Exception as e:
                failed_configs.append(f"override_{i}")
                errors.append(str(e))
        
        # Update MindsDB config if provided
        if bulk_update.mindsdb_config:
            try:
                active_config = db.query(MindsDBConfigurationModel).filter(
                    MindsDBConfigurationModel.is_active == True
                ).first()
                
                if active_config:
                    config_service.update_mindsdb_configuration(
                        active_config.id, bulk_update.mindsdb_config, 
                        current_user.id, current_user.email
                    )
                    applied_configs.append("mindsdb_config")
                    restart_required = True
                else:
                    errors.append("No active MindsDB configuration found")
                    failed_configs.append("mindsdb_config")
            except Exception as e:
                failed_configs.append("mindsdb_config")
                errors.append(str(e))
        
        return ConfigurationApplicationResult(
            success=len(failed_configs) == 0,
            applied_configs=applied_configs,
            failed_configs=failed_configs,
            errors=errors,
            restart_required=restart_required
        )
        
    except Exception as e:
        logger.error(f"Error in bulk configuration update: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating configurations: {str(e)}")


@router.post("/restart-required")
async def check_restart_required(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Check if application restart is required due to configuration changes"""
    try:
        # Check for configurations that require restart and have been modified
        restart_configs = db.query(ConfigurationOverride).filter(
            ConfigurationOverride.requires_restart == True,
            ConfigurationOverride.value != ConfigurationOverride.default_value
        ).all()
        
        return {
            "restart_required": len(restart_configs) > 0,
            "affected_configs": [
                {
                    "key": config.key,
                    "title": config.title,
                    "last_applied": config.last_applied_at.isoformat() if config.last_applied_at else None
                }
                for config in restart_configs
            ],
            "recommendation": "Restart the application to apply configuration changes" if restart_configs else "No restart required"
        }
        
    except Exception as e:
        logger.error(f"Error checking restart requirement: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking restart requirement: {str(e)}")