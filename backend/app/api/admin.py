from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.auth import get_current_superuser
from app.models.user import User
from app.models.config import Configuration
from app.models.dataset import Dataset
from app.models.analytics import DatasetAccess, SystemMetrics, AccessRequest, AuditLog
from app.schemas.config import Configuration as ConfigSchema, ConfigurationCreate, ConfigurationUpdate

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
        
        # Total datasets
        total_datasets = db.query(Dataset).count()
        
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
            "totalDatasets": total_datasets,
            "pendingRequests": pending_requests,
            "systemHealth": system_health,
            "recentActivity": recent_activity
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting admin stats: {str(e)}")