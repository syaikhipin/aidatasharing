"""
API Gateway Module for AI Share Platform
Handles gateway routing and management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gateway", tags=["gateway"])


@router.get("/health")
async def gateway_health():
    """Gateway health check endpoint"""
    return {
        "status": "healthy",
        "service": "gateway",
        "message": "Gateway service is running"
    }


@router.get("/info")
async def gateway_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get gateway information"""
    try:
        return {
            "gateway_version": "1.0.0",
            "available_services": [
                "auth",
                "organizations", 
                "datasets",
                "models",
                "mindsdb",
                "admin",
                "analytics",
                "data_access",
                "data_sharing",
                "file_handler",
                "data_connectors",
                "llm_configurations",
                "environment",
                "proxy_connectors"
            ],
            "user": current_user.email if current_user else None
        }
    except Exception as e:
        logger.error(f"Error getting gateway info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get gateway information"
        )