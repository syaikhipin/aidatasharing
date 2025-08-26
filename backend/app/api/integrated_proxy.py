"""
Integrated Proxy API endpoints that run within the main backend
Provides proxy functionality for both upload and connector data sharing modes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from app.core.database import get_db
from app.services.integrated_proxy_service import integrated_proxy

logger = logging.getLogger(__name__)

router = APIRouter()

@router.on_event("startup")
async def startup_event():
    """Start integrated proxy service on startup"""
    logger.info("Starting integrated proxy service...")

@router.get("/health")
async def proxy_health():
    """Health check for proxy service"""
    return {
        "status": "healthy",
        "service": "integrated_proxy",
        "timestamp": integrated_proxy.get_proxy_info()
    }

@router.get("/info")
async def proxy_info():
    """Get proxy service information"""
    return integrated_proxy.get_proxy_info()

@router.post("/start")
async def start_proxy_service(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start the integrated proxy service"""
    try:
        await integrated_proxy.start_proxy_service(background_tasks)
        return {
            "message": "Proxy service started successfully",
            "info": integrated_proxy.get_proxy_info()
        }
    except Exception as e:
        logger.error(f"Failed to start proxy service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_proxy_service(db: Session = Depends(get_db)):
    """Stop the integrated proxy service"""
    try:
        await integrated_proxy.stop_proxy_service()
        return {
            "message": "Proxy service stopped successfully"
        }
    except Exception as e:
        logger.error(f"Failed to stop proxy service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Database-specific proxy endpoints
@router.get("/mysql/{database_name}")
@router.post("/mysql/{database_name}")
async def mysql_proxy(
    database_name: str,
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = None
):
    """MySQL proxy endpoint"""
    return await integrated_proxy.handle_proxy_request(
        "mysql", database_name, request, db, token
    )

@router.get("/postgresql/{database_name}")
@router.post("/postgresql/{database_name}")
async def postgresql_proxy(
    database_name: str,
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = None
):
    """PostgreSQL proxy endpoint"""
    return await integrated_proxy.handle_proxy_request(
        "postgresql", database_name, request, db, token
    )

@router.get("/api/{api_name}")
@router.post("/api/{api_name}")
async def api_proxy(
    api_name: str,
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = None
):
    """API proxy endpoint"""
    return await integrated_proxy.handle_proxy_request(
        "api", api_name, request, db, token
    )

@router.get("/clickhouse/{database_name}")
@router.post("/clickhouse/{database_name}")
async def clickhouse_proxy(
    database_name: str,
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = None
):
    """ClickHouse proxy endpoint"""
    return await integrated_proxy.handle_proxy_request(
        "clickhouse", database_name, request, db, token
    )

@router.get("/mongodb/{database_name}")
@router.post("/mongodb/{database_name}")
async def mongodb_proxy(
    database_name: str,
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = None
):
    """MongoDB proxy endpoint"""
    return await integrated_proxy.handle_proxy_request(
        "mongodb", database_name, request, db, token
    )

@router.get("/s3/{database_name}")
@router.post("/s3/{database_name}")
async def s3_proxy(
    database_name: str,
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = None
):
    """S3 proxy endpoint"""
    return await integrated_proxy.handle_proxy_request(
        "s3", database_name, request, db, token
    )

# Shared link access endpoints
@router.get("/shared/{share_id}")
@router.post("/shared/{share_id}")
async def shared_link_access(
    share_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Access shared link through integrated proxy"""
    return await integrated_proxy.handle_share_access(share_id, request, db)

# Generic proxy endpoint that auto-detects type
@router.get("/{proxy_type}/{database_name}")
@router.post("/{proxy_type}/{database_name}")
async def generic_proxy(
    proxy_type: str,
    database_name: str,
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = None
):
    """Generic proxy endpoint that handles any supported type"""
    
    # Validate proxy type
    supported_types = ["mysql", "postgresql", "api", "clickhouse", "mongodb", "s3", "shared"]
    if proxy_type not in supported_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported proxy type: {proxy_type}. Supported types: {', '.join(supported_types)}"
        )
    
    return await integrated_proxy.handle_proxy_request(
        proxy_type, database_name, request, db, token
    )