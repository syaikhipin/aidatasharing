from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid
import logging
import os
import mimetypes

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.dataset import Dataset, ShareAccessSession
from app.services.data_sharing import DataSharingService
from app.services.mindsdb import MindsDBService

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


# Pydantic models for request/response
class CreateShareLinkRequest(BaseModel):
    dataset_id: int
    expires_in_hours: Optional[int] = None
    password: Optional[str] = None
    enable_chat: bool = True


class CreateChatSessionRequest(BaseModel):
    share_token: str


class SendChatMessageRequest(BaseModel):
    session_token: str
    message: str


class AccessSharedDatasetRequest(BaseModel):
    password: Optional[str] = None


class ShareChatRequest(BaseModel):
    message: str
    session_token: Optional[str] = None


# Data sharing endpoints
@router.post("/create-share-link")
async def create_share_link(
    request: CreateShareLinkRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create a shareable link for a dataset."""
    service = DataSharingService(db)
    
    return service.create_share_link(
        dataset_id=request.dataset_id,
        user_id=current_user.id,
        expires_in_hours=request.expires_in_hours,
        password=request.password,
        enable_chat=request.enable_chat
    )


@router.get("/shared/{share_token}")
async def get_shared_dataset(
    share_token: str,
    request: Request,
    password: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Access a shared dataset via share token."""
    service = DataSharingService(db)
    
    # Get client info
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent")
    
    return await service.get_shared_dataset(
        share_token=share_token,
        password=password,
        ip_address=ip_address,
        user_agent=user_agent
    )


@router.post("/shared/{share_token}/access")
async def access_shared_dataset_with_password(
    share_token: str,
    request_data: AccessSharedDatasetRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Access a password-protected shared dataset."""
    service = DataSharingService(db)
    
    # Get client info
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent")
    
    return await service.get_shared_dataset(
        share_token=share_token,
        password=request_data.password,
        ip_address=ip_address,
        user_agent=user_agent
    )


# Chat functionality endpoints
@router.post("/chat/create-session")
async def create_chat_session(
    request_data: CreateChatSessionRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create a new chat session for a shared dataset."""
    service = DataSharingService(db)
    
    # Get client info
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent")
    
    return service.create_chat_session(
        share_token=request_data.share_token,
        ip_address=ip_address,
        user_agent=user_agent
    )


@router.post("/chat/message")
async def send_chat_message(
    request_data: SendChatMessageRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Send a message in a chat session."""
    service = DataSharingService(db)
    
    return service.send_chat_message(
        session_token=request_data.session_token,
        message=request_data.message
    )


@router.get("/chat/{session_token}/history")
async def get_chat_history(
    session_token: str,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get chat history for a session."""
    service = DataSharingService(db)
    
    return service.get_chat_history(session_token)


@router.delete("/chat/{session_token}")
async def end_chat_session(
    session_token: str,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """End a chat session."""
    service = DataSharingService(db)
    
    success = service.end_chat_session(session_token)
    
    if success:
        return {"message": "Chat session ended successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )


# Analytics endpoints
@router.get("/analytics/{dataset_id}")
async def get_dataset_analytics(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get analytics for a shared dataset."""
    service = DataSharingService(db)
    
    return service.get_dataset_analytics(dataset_id, current_user.id)


@router.get("/my-shared-datasets")
async def get_my_shared_datasets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all datasets shared by the current user."""
    from app.models.dataset import Dataset
    
    datasets = db.query(Dataset).filter(
        Dataset.owner_id == current_user.id,
        Dataset.public_share_enabled == True
    ).all()
    
    return [
        {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "share_token": dataset.share_token,
            "share_url": f"/shared/{dataset.share_token}",
            "expires_at": dataset.share_expires_at,
            "view_count": dataset.share_view_count,
            "chat_enabled": dataset.ai_chat_enabled,
            "password_protected": bool(dataset.share_password),
            "created_at": dataset.created_at,
            "last_accessed": dataset.last_accessed,
            "sharing_level": dataset.sharing_level.value if dataset.sharing_level else "private",
            "type": dataset.type.value if dataset.type else None,
            "size_bytes": dataset.size_bytes
        }
        for dataset in datasets
    ]


@router.post("/refresh-proxy-connectors")
async def refresh_proxy_connectors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Refresh proxy connectors for all shared datasets."""
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    service = DataSharingService(db)
    
    # Get all shared datasets in user's organization
    shared_datasets = db.query(Dataset).filter(
        Dataset.organization_id == current_user.organization_id,
        Dataset.public_share_enabled == True,
        Dataset.share_token.isnot(None),
        Dataset.is_deleted == False
    ).all()
    
    created_connectors = []
    for dataset in shared_datasets:
        try:
            connector = await service._create_dataset_proxy_connector(dataset, dataset.share_token)
            if connector:
                created_connectors.append({
                    "dataset_name": dataset.name,
                    "proxy_id": connector.proxy_id,
                    "connector_id": connector.id
                })
        except Exception as e:
            logger.error(f"Failed to create connector for dataset {dataset.name}: {e}")
    
    return {
        "message": f"Created {len(created_connectors)} proxy connectors",
        "connectors": created_connectors
    }

@router.delete("/shared/{dataset_id}/disable")
async def disable_sharing(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Disable sharing for a dataset."""
    from app.models.dataset import Dataset
    
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.owner_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Disable sharing
    dataset.public_share_enabled = False
    dataset.share_token = None
    dataset.share_expires_at = None
    dataset.share_password = None
    dataset.ai_chat_enabled = False
    
    # Also disable related proxy connector
    from app.models.proxy_connector import ProxyConnector
    proxy_connector = db.query(ProxyConnector).filter(
        ProxyConnector.name == dataset.name,
        ProxyConnector.organization_id == dataset.organization_id
    ).first()
    
    if proxy_connector:
        proxy_connector.is_active = False
    
    db.commit()
    
    return {"message": "Sharing disabled successfully"}


# Public endpoints (no authentication required)
@router.get("/public/shared/{share_token}/info")
async def get_shared_dataset_info(
    share_token: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get basic information about a shared dataset (no password required)."""
    dataset = db.query(Dataset).filter(
        Dataset.share_token == share_token,
        Dataset.public_share_enabled == True,
        Dataset.is_deleted == False
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared dataset not found"
        )
    
    # Check expiration
    if dataset.share_expires_at and dataset.share_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Share link has expired"
        )
    
    return {
        "name": dataset.name,
        "description": dataset.description,
        "type": dataset.type,
        "size_bytes": dataset.size_bytes,
        "row_count": dataset.row_count,
        "column_count": dataset.column_count,
        "password_protected": bool(dataset.share_password),
        "chat_enabled": dataset.ai_chat_enabled,
        "allow_download": dataset.allow_download,
        "created_at": dataset.created_at,
        "expires_at": dataset.share_expires_at,
        "view_count": dataset.share_view_count
    }


@router.get("/public/shared/{share_token}")
async def access_shared_dataset_public(
    share_token: str,
    password: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Access a shared dataset via share token (public endpoint)."""
    service = DataSharingService(db)
    
    # Get client info
    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None
    
    # Get dataset info directly without creating sessions
    dataset_info = await service.get_shared_dataset(
        share_token=share_token,
        password=password,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return dataset_info


@router.post("/public/shared/{share_token}/chat")
async def chat_with_shared_dataset(
    share_token: str,
    chat_request: ShareChatRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Chat with a shared dataset (public endpoint)."""
    # Verify dataset and access
    dataset = db.query(Dataset).filter(
        Dataset.share_token == share_token,
        Dataset.public_share_enabled == True,
        Dataset.ai_chat_enabled == True,
        Dataset.is_deleted == False
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared dataset not found or chat not enabled"
        )
    
    # Check expiration
    if dataset.share_expires_at and dataset.share_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Share link has expired"
        )
    
    # Verify session if provided
    session = None
    if chat_request.session_token:
        session = db.query(ShareAccessSession).filter(
            ShareAccessSession.session_token == chat_request.session_token,
            ShareAccessSession.dataset_id == dataset.id,
            ShareAccessSession.is_active == True
        ).first()
        
        if session:
            # Check session expiration
            if session.expires_at and session.expires_at < datetime.utcnow():
                session.is_active = False
                db.commit()
                session = None
    
    # Use MindsDB service for chat
    mindsdb_service = MindsDBService()
    try:
        chat_response = mindsdb_service.chat_with_dataset(
            dataset_id=str(dataset.id),
            message=chat_request.message,
            user_id=None,  # Anonymous user
            session_id=chat_request.session_token,
            organization_id=dataset.organization_id
        )
        
        # Update session activity
        if session:
            session.chat_messages_sent += 1
            session.last_activity_at = datetime.utcnow()
            db.commit()
        
        return chat_response
        
    except Exception as e:
        logger.error(f"Chat failed for shared dataset {dataset.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat service error: {str(e)}"
        )


@router.get("/public/shared/{share_token}/download")
async def download_shared_dataset(
    share_token: str,
    password: Optional[str] = None,
    session_token: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Download a shared dataset (public endpoint)."""
    # Verify dataset and access
    dataset = db.query(Dataset).filter(
        Dataset.share_token == share_token,
        Dataset.public_share_enabled == True,
        Dataset.allow_download == True,
        Dataset.is_deleted == False
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared dataset not found or download not allowed"
        )
    
    # Check expiration
    if dataset.share_expires_at and dataset.share_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Share link has expired"
        )
    
    # Check password if required
    if dataset.share_password and dataset.share_password != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Update session if provided
    if session_token:
        session = db.query(ShareAccessSession).filter(
            ShareAccessSession.session_token == session_token,
            ShareAccessSession.dataset_id == dataset.id,
            ShareAccessSession.is_active == True
        ).first()
        
        if session:
            session.files_downloaded += 1
            session.last_activity_at = datetime.utcnow()
            db.commit()
    
    # Check if this is a URL (external dataset) - cannot download
    if dataset.source_url.startswith(('http://', 'https://')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot download external URL datasets. This dataset is hosted externally."
        )
    
    # Construct file path - files are stored in backend/storage/
    file_path = None
    possible_paths = [
        f"storage/{dataset.source_url}",  # Main storage directory (backend/storage/)
        f"../storage/{dataset.source_url}",  # Alternative storage path
        dataset.source_url,  # Direct path (if absolute)
        f"uploads/{dataset.source_url}",  # Legacy uploads directory
    ]
    
    for path in possible_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            file_path = abs_path
            break
    
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = f"application/{dataset.type}" if dataset.type else "application/octet-stream"
    
    # Create appropriate filename
    filename = f"{dataset.name}.{dataset.type}" if dataset.type else dataset.name
    
    # Return file response
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=mime_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )
@router.get("/shared/{share_token}/download")
async def download_shared_dataset_authenticated(
    share_token: str,
    password: Optional[str] = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a shared dataset (authenticated endpoint)."""
    # Verify dataset and access
    dataset = db.query(Dataset).filter(
        Dataset.share_token == share_token,
        Dataset.public_share_enabled == True,
        Dataset.allow_download == True,
        Dataset.is_deleted == False
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared dataset not found or download not allowed"
        )
    
    # Check expiration
    if dataset.share_expires_at and dataset.share_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Share link has expired"
        )
    
    # Check password if required
    if dataset.share_password and dataset.share_password != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Check if this is a URL (external dataset) - cannot download
    if dataset.source_url.startswith(('http://', 'https://')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot download external URL datasets. This dataset is hosted externally."
        )
    
    # Construct file path - files are stored in backend/storage/
    file_path = None
    possible_paths = [
        f"storage/{dataset.source_url}",  # Main storage directory (backend/storage/)
        f"../storage/{dataset.source_url}",  # Alternative storage path
        dataset.source_url,  # Direct path (if absolute)
        f"uploads/{dataset.source_url}",  # Legacy uploads directory
    ]
    
    for path in possible_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            file_path = abs_path
            break
    
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = f"application/{dataset.type}" if dataset.type else "application/octet-stream"
    
    # Create appropriate filename
    filename = f"{dataset.name}.{dataset.type}" if dataset.type else dataset.name
    
    # Return file response
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=mime_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

