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


class DownloadSelectedFilesRequest(BaseModel):
    file_ids: List[int]


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


@router.post("/validate-shared-resources")
async def validate_shared_resources(
    resource_tokens: Dict[str, List[str]],  # e.g., {"share_tokens": ["token1", "token2"], "proxy_ids": ["id1", "id2"]}
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Validate multiple shared resources at once for frontend validation."""
    validation_results = {
        "share_tokens": {},
        "proxy_connectors": {},
        "validation_timestamp": datetime.utcnow().isoformat()
    }
    
    # Validate share tokens
    if "share_tokens" in resource_tokens:
        for token in resource_tokens["share_tokens"]:
            try:
                dataset = db.query(Dataset).filter(
                    Dataset.share_token == token,
                    Dataset.public_share_enabled == True,
                    Dataset.is_deleted == False,
                    Dataset.is_active == True
                ).first()
                
                if dataset:
                    # No longer checking expiration - share links don't expire
                    is_expired = False
                    
                    # Check connector if exists
                    connector_valid = True
                    if dataset.connector_id:
                        connector = db.query(Dataset.__table__.c.connector_id).filter(
                            Dataset.id == dataset.id
                        ).first()
                        if connector:
                            from app.models.dataset import DatabaseConnector
                            connector_obj = db.query(DatabaseConnector).filter(
                                DatabaseConnector.id == dataset.connector_id,
                                DatabaseConnector.is_deleted == False,
                                DatabaseConnector.is_active == True
                            ).first()
                            connector_valid = connector_obj is not None
                    
                    # Check file exists for uploaded datasets
                    file_valid = True
                    if dataset.file_path and not dataset.connector_id:
                        file_valid = os.path.exists(dataset.file_path)
                    
                    validation_results["share_tokens"][token] = {
                        "valid": not is_expired and connector_valid and file_valid,
                        "dataset_name": dataset.name,
                        "is_expired": is_expired,
                        "connector_valid": connector_valid,
                        "file_valid": file_valid,
                        "dataset_type": dataset.type.value if dataset.type else None
                    }
                else:
                    validation_results["share_tokens"][token] = {
                        "valid": False,
                        "error": "Dataset not found or sharing disabled"
                    }
            except Exception as e:
                validation_results["share_tokens"][token] = {
                    "valid": False,
                    "error": f"Validation error: {str(e)}"
                }
    
    # Validate proxy connectors
    if "proxy_ids" in resource_tokens:
        for proxy_id in resource_tokens["proxy_ids"]:
            try:
                from app.models.proxy_connector import ProxyConnector
                proxy = db.query(ProxyConnector).filter(
                    ProxyConnector.proxy_id == proxy_id,
                    ProxyConnector.is_active == True
                ).first()
                
                if proxy:
                    validation_results["proxy_connectors"][proxy_id] = {
                        "valid": True,
                        "name": proxy.name,
                        "connector_type": proxy.connector_type,
                        "is_public": proxy.is_public,
                        "proxy_url": proxy.proxy_url
                    }
                else:
                    validation_results["proxy_connectors"][proxy_id] = {
                        "valid": False,
                        "error": "Proxy connector not found or inactive"
                    }
            except Exception as e:
                validation_results["proxy_connectors"][proxy_id] = {
                    "valid": False,
                    "error": f"Validation error: {str(e)}"
                }
    
    return validation_results


@router.get("/my-shared-datasets")
async def get_my_shared_datasets(
    include_invalid: bool = True,  # Changed default to True to be less aggressive
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all datasets shared by the current user with validity checks."""
    from app.models.dataset import Dataset
    
    datasets = db.query(Dataset).filter(
        Dataset.owner_id == current_user.id,
        Dataset.public_share_enabled == True,
        Dataset.is_deleted == False,
        Dataset.is_active == True
    ).all()
    
    result = []
    
    for dataset in datasets:
        # No longer checking expiration - share links don't expire
        is_expired = False
        
        # Check connector validity
        connector_valid = True
        if dataset.connector_id:
            from app.models.dataset import DatabaseConnector
            connector = db.query(DatabaseConnector).filter(
                DatabaseConnector.id == dataset.connector_id,
                DatabaseConnector.is_deleted == False,
                DatabaseConnector.is_active == True
            ).first()
            connector_valid = connector is not None
        
        # Check file validity - but be more lenient for different dataset types
        file_valid = True
        if dataset.file_path and not dataset.connector_id:
            # Use proper storage path resolution
            from app.services.storage import StorageService
            try:
                storage_service = StorageService()
                # Get the actual storage base path from storage service
                if hasattr(storage_service, 'backend') and hasattr(storage_service.backend, 'storage_dir'):
                    storage_base = storage_service.backend.storage_dir
                else:
                    from app.core.config import settings
                    storage_base = os.path.abspath(settings.STORAGE_BASE_PATH)
                
                full_path = os.path.join(storage_base, dataset.file_path)
                file_valid = os.path.exists(full_path)
                logger.debug(f"File validation for dataset {dataset.id}: {full_path} exists: {file_valid}")
            except Exception as e:
                # Fallback to direct path check if storage service fails
                logger.warning(f"Storage service validation failed for dataset {dataset.id}: {e}")
                file_valid = os.path.exists(dataset.file_path)
        elif not dataset.file_path and not dataset.connector_id:
            # For datasets without file_path or connector_id, check if it has dataset_files
            from app.models.dataset import DatasetFile
            has_dataset_files = db.query(DatasetFile).filter(
                DatasetFile.dataset_id == dataset.id,
                DatasetFile.is_deleted == False
            ).first() is not None
            file_valid = has_dataset_files
        
        is_valid = not is_expired and connector_valid and file_valid
        
        # Don't automatically disable sharing - just log warnings for invalid datasets
        if not is_valid:
            logger.warning(f"Dataset {dataset.id} ({dataset.name}) has validation issues: expired={is_expired}, connector_valid={connector_valid}, file_valid={file_valid}")
            # Only skip if include_invalid is False
            if not include_invalid:
                continue
        
        dataset_info = {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "share_token": dataset.share_token,
            "share_url": f"/shared/{dataset.share_token}",
            "view_count": dataset.share_view_count,
            "chat_enabled": dataset.ai_chat_enabled,
            "password_protected": bool(dataset.share_password),
            "created_at": dataset.created_at,
            "last_accessed": dataset.last_accessed,
            "sharing_level": dataset.sharing_level.value if dataset.sharing_level else "private",
            "type": dataset.type.value if dataset.type else None,
            "size_bytes": dataset.size_bytes,
            "is_valid": is_valid,
            "validation_details": {
                "is_expired": is_expired,
                "connector_valid": connector_valid,
                "file_valid": file_valid
            } if include_invalid else None
        }
        
        result.append(dataset_info)
    
    return result


@router.post("/refresh-proxy-connectors")
async def refresh_proxy_connectors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Refresh proxy connectors for all shared datasets."""
    # Check if user has admin privileges or is superuser
    if not (current_user.role in ["owner", "admin"] or getattr(current_user, 'is_superuser', False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin or owner role required."
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
    # Expiration functionality removed - share links no longer expire
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
    # No longer checking expiration - share links don't expire
    if False:
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
        # Expiration functionality removed
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
    # No longer checking expiration - share links don't expire
    if False:
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
    # No longer checking expiration - share links don't expire
    if False:
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
    if dataset.source_url and dataset.source_url.startswith(('http://', 'https://')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot download external URL datasets. This dataset is hosted externally."
        )
    
    # Try to find the file using multiple methods
    file_path = None
    
    # Method 1: Check dataset_files table first (new upload system)
    if dataset.is_multi_file_dataset or not dataset.source_url:
        from app.models.dataset import DatasetFile
        dataset_files = db.query(DatasetFile).filter(
            DatasetFile.dataset_id == dataset.id,
            DatasetFile.is_deleted == False
        ).all()
        
        if dataset_files:
            # For single file, use the first/primary file
            primary_file = next((f for f in dataset_files if f.is_primary), dataset_files[0])
            if primary_file.file_path and os.path.exists(primary_file.file_path):
                file_path = primary_file.file_path
    
    # Method 2: Use source_url if available
    if not file_path and dataset.source_url:
        possible_paths = [
            f"storage/{dataset.source_url}",  # Main storage directory
            f"../storage/{dataset.source_url}",  # Alternative storage path
            dataset.source_url,  # Direct path (if absolute)
            f"uploads/{dataset.source_url}",  # Legacy uploads directory
        ]
        
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                file_path = abs_path
                break
    
    # Method 3: Search by dataset ID pattern if still not found
    if not file_path:
        import glob
        
        # Search for files with dataset ID in the filename
        search_patterns = [
            f"storage/*/dataset_{dataset.id}_*",
            f"../storage/*/dataset_{dataset.id}_*", 
            f"storage/dataset_{dataset.id}_*",
            f"../storage/dataset_{dataset.id}_*"
        ]
        
        for pattern in search_patterns:
            matches = glob.glob(pattern)
            if matches:
                # Use the first match found
                file_path = os.path.abspath(matches[0])
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
    # No longer checking expiration - share links don't expire
    if False:
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
    if dataset.source_url and dataset.source_url.startswith(('http://', 'https://')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot download external URL datasets. This dataset is hosted externally."
        )
    
    # Try to find the file using multiple methods (same as public endpoint)
    file_path = None
    
    # Method 1: Check dataset_files table first (new upload system)
    if dataset.is_multi_file_dataset or not dataset.source_url:
        from app.models.dataset import DatasetFile
        dataset_files = db.query(DatasetFile).filter(
            DatasetFile.dataset_id == dataset.id,
            DatasetFile.is_deleted == False
        ).all()
        
        if dataset_files:
            # For single file, use the first/primary file
            primary_file = next((f for f in dataset_files if f.is_primary), dataset_files[0])
            if primary_file.file_path and os.path.exists(primary_file.file_path):
                file_path = primary_file.file_path
    
    # Method 2: Use source_url if available
    if not file_path and dataset.source_url:
        possible_paths = [
            f"storage/{dataset.source_url}",  # Main storage directory
            f"../storage/{dataset.source_url}",  # Alternative storage path
            dataset.source_url,  # Direct path (if absolute)
            f"uploads/{dataset.source_url}",  # Legacy uploads directory
        ]
        
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                file_path = abs_path
                break
    
    # Method 3: Search by dataset ID pattern if still not found
    if not file_path:
        import glob
        
        # Search for files with dataset ID in the filename
        search_patterns = [
            f"storage/*/dataset_{dataset.id}_*",
            f"../storage/*/dataset_{dataset.id}_*", 
            f"storage/dataset_{dataset.id}_*",
            f"../storage/dataset_{dataset.id}_*"
        ]
        
        for pattern in search_patterns:
            matches = glob.glob(pattern)
            if matches:
                # Use the first match found
                file_path = os.path.abspath(matches[0])
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

