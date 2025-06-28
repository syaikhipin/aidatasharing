from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.data_sharing import DataSharingService


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
    
    return service.get_shared_dataset(
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
    
    return service.get_shared_dataset(
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
            "last_accessed": dataset.last_accessed
        }
        for dataset in datasets
    ]


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
    
    db.commit()
    
    return {"message": "Sharing disabled successfully"}


# Public endpoints (no authentication required)
@router.get("/public/shared/{share_token}/info")
async def get_shared_dataset_info(
    share_token: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get basic info about a shared dataset (public endpoint)."""
    from app.models.dataset import Dataset
    from datetime import datetime
    
    dataset = db.query(Dataset).filter(
        Dataset.share_token == share_token,
        Dataset.public_share_enabled == True
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
        "chat_enabled": dataset.ai_chat_enabled,
        "password_protected": bool(dataset.share_password),
        "expires_at": dataset.share_expires_at,
        "created_at": dataset.created_at
    } 