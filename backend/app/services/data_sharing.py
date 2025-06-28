from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.user import User
from app.models.dataset import Dataset, DatasetAccessLog, DatasetChatSession, ChatMessage, DatasetShareAccess
from app.models.organization import Organization, Department, DataSharingLevel, UserRole
from datetime import datetime, timedelta
import logging
import secrets
import hashlib
from fastapi import HTTPException, status
from app.core.config import settings
from app.services.mindsdb import MindsDBService

logger = logging.getLogger(__name__)


class DataSharingService:
    """Service for managing organization-scoped data sharing and access control"""
    
    def __init__(self, db: Session):
        self.db = db
        self.mindsdb_service = MindsDBService()
    
    def can_access_dataset(self, user: User, dataset: Dataset) -> bool:
        """
        Check if a user can access a dataset within their organization.
        All data sharing is organization-scoped only.
        """
        # Users can only access datasets from their own organization
        if not user.organization_id or user.organization_id != dataset.organization_id:
            return False
        
        # Owner can always access their own datasets
        if dataset.owner_id == user.id:
            return True
        
        # Check sharing level within the organization
        if dataset.sharing_level == DataSharingLevel.PRIVATE:
            return False
        
        elif dataset.sharing_level == DataSharingLevel.ORGANIZATION:
            # All organization members can access
            return True
        
        elif dataset.sharing_level == DataSharingLevel.DEPARTMENT:
            # Only department members can access
            return (user.department_id and 
                   user.department_id == dataset.department_id)
        
        return False
    
    def get_accessible_datasets(self, user: User, 
                              sharing_level: Optional[DataSharingLevel] = None) -> List[Dataset]:
        """
        Get all datasets accessible to a user within their organization.
        """
        if not user.organization_id:
            return []
        
        query = self.db.query(Dataset).filter(
            Dataset.organization_id == user.organization_id
        )
        
        # Filter by sharing level if specified
        if sharing_level:
            query = query.filter(Dataset.sharing_level == sharing_level)
        
        datasets = query.all()
        
        # Filter based on access permissions
        accessible_datasets = []
        for dataset in datasets:
            if self.can_access_dataset(user, dataset):
                accessible_datasets.append(dataset)
        
        return accessible_datasets
    
    def get_organization_datasets(self, organization_id: int, 
                                user: User) -> List[Dataset]:
        """
        Get all datasets for an organization (admin/manager view).
        Only organization admins/owners can see all datasets.
        """
        if (not user.organization_id or 
            user.organization_id != organization_id or
            user.role not in ["owner", "admin"]):
            return []
        
        return self.db.query(Dataset).filter(
            Dataset.organization_id == organization_id
        ).all()
    
    def log_access(self, user: User, dataset: Dataset, access_type: str,
                   ip_address: Optional[str] = None, 
                   user_agent: Optional[str] = None) -> bool:
        """Log dataset access for audit purposes"""
        if not self.can_access_dataset(user, dataset):
            return False
        
        access_log = DatasetAccessLog(
            dataset_id=dataset.id,
            user_id=user.id,
            access_type=access_type,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(access_log)
        self.db.commit()
        
        # Update last accessed timestamp
        dataset.last_accessed = access_log.created_at
        self.db.commit()
        
        return True
    
    def get_organization_stats(self, organization_id: int, user: User) -> dict:
        """
        Get organization data usage statistics.
        Only available to organization admins/owners.
        """
        if (not user.organization_id or 
            user.organization_id != organization_id or
            user.role not in ["owner", "admin"]):
            return {}
        
        datasets = self.db.query(Dataset).filter(
            Dataset.organization_id == organization_id
        ).all()
        
        total_datasets = len(datasets)
        
        # Count by sharing level
        sharing_stats = {
            DataSharingLevel.ORGANIZATION: 0,
            DataSharingLevel.DEPARTMENT: 0,
            DataSharingLevel.PRIVATE: 0
        }
        
        total_size = 0
        for dataset in datasets:
            sharing_stats[dataset.sharing_level] += 1
            if dataset.size_bytes:
                total_size += dataset.size_bytes
        
        # Recent access count
        recent_accesses = self.db.query(DatasetAccessLog).join(Dataset).filter(
            Dataset.organization_id == organization_id
        ).count()
        
        return {
            "total_datasets": total_datasets,
            "total_size_bytes": total_size,
            "sharing_levels": sharing_stats,
            "recent_accesses": recent_accesses,
            "organization_id": organization_id
        }
    
    def check_department_access(self, user: User, department_id: int) -> bool:
        """Check if user can access department-level data"""
        return (user.department_id == department_id and 
               user.organization_id is not None)
    
    def validate_dataset_creation(self, user: User, organization_id: int) -> bool:
        """
        Validate if user can create dataset in the organization.
        Users can only create datasets in their own organization.
        """
        return (user.organization_id == organization_id and
               user.role in ["owner", "admin", "manager", "member"])
    
    def update_sharing_level(self, user: User, dataset: Dataset, 
                           new_sharing_level: DataSharingLevel) -> bool:
        """
        Update dataset sharing level within organization.
        Only owner and admins can change sharing levels.
        """
        # Check permissions
        if not (dataset.owner_id == user.id or 
               (user.organization_id == dataset.organization_id and 
                user.role in ["owner", "admin"])):
            return False
        
        dataset.sharing_level = new_sharing_level
        self.db.commit()
        
        logger.info(f"Dataset {dataset.id} sharing level updated to {new_sharing_level} by user {user.id}")
        return True
    
    def get_sharing_stats(self, organization_id: int, user: User) -> dict:
        """
        Get data sharing statistics for an organization (organization-scoped only)
        """
        if (not user.organization_id or 
            user.organization_id != organization_id or
            user.role not in ["owner", "admin"]):
            return {}
        
        # Get datasets by sharing level
        datasets = self.db.query(Dataset).filter(
            Dataset.organization_id == organization_id
        ).all()
        
        stats = {
            "total_datasets": len(datasets),
            "by_sharing_level": {
                "private": 0,
                "department": 0,
                "organization": 0
            },
            "by_type": {},
            "total_access_logs": 0,
            "unique_users_accessed": 0
        }
        
        # Count by sharing level (no public level)
        for dataset in datasets:
            level = dataset.sharing_level.value if dataset.sharing_level else "private"
            if level in stats["by_sharing_level"]:
                stats["by_sharing_level"][level] += 1
            
            # Count by type
            dataset_type = dataset.type.value if dataset.type else "unknown"
            stats["by_type"][dataset_type] = stats["by_type"].get(dataset_type, 0) + 1
        
        # Get access statistics
        access_logs = self.db.query(DatasetAccessLog).join(Dataset).filter(
            Dataset.organization_id == organization_id
        ).all()
        
        stats["total_access_logs"] = len(access_logs)
        stats["unique_users_accessed"] = len(set(log.user_id for log in access_logs))
        
        return stats
    
    def get_department_datasets(
        self, 
        department_id: int, 
        user: User
    ) -> List[Dataset]:
        """
        Get datasets shared within a specific department
        """
        # Check if user has access to this department
        if (not user.organization_id or 
            user.department_id != department_id and
            user.role not in ["owner", "admin"]):
            return []
        
        return self.db.query(Dataset).filter(
            Dataset.department_id == department_id,
            Dataset.sharing_level == DataSharingLevel.DEPARTMENT
        ).all()
    
    def get_organization_shared_datasets(
        self, 
        organization_id: int, 
        user: User
    ) -> List[Dataset]:
        """
        Get all datasets shared at organization level (organization-scoped only)
        """
        # Check if user has access to this organization
        if (not user.organization_id or 
            user.organization_id != organization_id):
            return []
        
        return self.db.query(Dataset).filter(
            Dataset.organization_id == organization_id,
            Dataset.sharing_level == DataSharingLevel.ORGANIZATION
        ).all()

    def create_share_link(
        self,
        dataset_id: int,
        user_id: int,
        expires_in_hours: Optional[int] = None,
        password: Optional[str] = None,
        enable_chat: bool = True
    ) -> Dict[str, Any]:
        """Create a shareable link for a dataset."""
        dataset = self.db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.owner_id == user_id
        ).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found or access denied"
            )
        
        # Generate unique share token
        share_token = self._generate_share_token(dataset_id, user_id)
        
        # Set expiration
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        elif settings.SHARE_LINK_EXPIRY_HOURS > 0:
            expires_at = datetime.utcnow() + timedelta(hours=settings.SHARE_LINK_EXPIRY_HOURS)
        
        # Update dataset with sharing information
        dataset.public_share_enabled = True
        dataset.share_token = share_token
        dataset.share_expires_at = expires_at
        dataset.share_password = password
        dataset.ai_chat_enabled = enable_chat and settings.ENABLE_AI_CHAT
        
        self.db.commit()
        self.db.refresh(dataset)
        
        # Initialize AI context if chat is enabled
        if dataset.ai_chat_enabled:
            self._initialize_ai_context(dataset)
        
        share_url = f"/shared/{share_token}"
        
        return {
            "share_token": share_token,
            "share_url": share_url,
            "expires_at": expires_at,
            "chat_enabled": dataset.ai_chat_enabled,
            "password_protected": bool(password),
            "dataset_name": dataset.name
        }

    def get_shared_dataset(
        self,
        share_token: str,
        password: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get dataset information via share token."""
        dataset = self.db.query(Dataset).filter(
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
        
        # Check password if required
        if dataset.share_password and dataset.share_password != password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )
        
        # Log access
        self._log_share_access(dataset, share_token, ip_address, user_agent)
        
        # Update view count
        dataset.share_view_count += 1
        dataset.last_accessed = datetime.utcnow()
        self.db.commit()
        
        return {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "type": dataset.type,
            "size_bytes": dataset.size_bytes,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "schema_info": dataset.schema_info,
            "ai_summary": dataset.ai_summary,
            "ai_insights": dataset.ai_insights,
            "chat_enabled": dataset.ai_chat_enabled,
            "allow_download": dataset.allow_download,
            "created_at": dataset.created_at,
            "share_token": share_token
        }

    def create_chat_session(
        self,
        share_token: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new chat session for a shared dataset."""
        dataset = self.db.query(Dataset).filter(
            Dataset.share_token == share_token,
            Dataset.public_share_enabled == True,
            Dataset.ai_chat_enabled == True
        ).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found or chat not enabled"
            )
        
        # Check session limits
        active_sessions = self.db.query(DatasetChatSession).filter(
            DatasetChatSession.dataset_id == dataset.id,
            DatasetChatSession.is_active == True
        ).count()
        
        if active_sessions >= settings.MAX_CHAT_SESSIONS_PER_DATASET:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Maximum chat sessions reached for this dataset"
            )
        
        # Create session
        session_token = self._generate_session_token()
        system_prompt = self._generate_system_prompt(dataset)
        
        chat_session = DatasetChatSession(
            dataset_id=dataset.id,
            user_id=user_id,
            session_token=session_token,
            share_token=share_token,
            ip_address=ip_address,
            user_agent=user_agent,
            ai_model_name=dataset.chat_model_name or settings.DEFAULT_GEMINI_MODEL,
            system_prompt=system_prompt,
            context_data=dataset.chat_context
        )
        
        self.db.add(chat_session)
        self.db.commit()
        self.db.refresh(chat_session)
        
        return {
            "session_token": session_token,
                            "model_name": chat_session.ai_model_name,
            "dataset_name": dataset.name,
            "system_prompt": system_prompt
        }

    def send_chat_message(
        self,
        session_token: str,
        message: str,
        message_type: str = "user"
    ) -> Dict[str, Any]:
        """Send a message in a chat session."""
        session = self.db.query(DatasetChatSession).filter(
            DatasetChatSession.session_token == session_token,
            DatasetChatSession.is_active == True
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        dataset = session.dataset
        
        # Save user message
        user_message = ChatMessage(
            session_id=session.id,
            message_type=message_type,
            content=message,
            created_at=datetime.utcnow()
        )
        self.db.add(user_message)
        
        try:
            # Get AI response
            start_time = datetime.utcnow()
            ai_response = self._get_ai_response(dataset, session, message)
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Save AI response
            ai_message = ChatMessage(
                session_id=session.id,
                message_type="assistant",
                content=ai_response["content"],
                message_metadata=ai_response.get("metadata"),
                tokens_used=ai_response.get("tokens_used"),
                processing_time_ms=processing_time,
                model_version=session.ai_model_name,
                created_at=datetime.utcnow()
            )
            self.db.add(ai_message)
            
            # Update session stats
            session.message_count += 2  # user + assistant
            session.total_tokens_used += ai_response.get("tokens_used", 0)
            session.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            return {
                "user_message": {
                    "id": user_message.id,
                    "content": user_message.content,
                    "type": user_message.message_type,
                    "created_at": user_message.created_at
                },
                "ai_response": {
                    "id": ai_message.id,
                    "content": ai_message.content,
                    "type": ai_message.message_type,
                    "tokens_used": ai_message.tokens_used,
                    "processing_time_ms": ai_message.processing_time_ms,
                    "created_at": ai_message.created_at
                }
            }
            
        except Exception as e:
            self.db.rollback()
            # Save error message
            error_message = ChatMessage(
                session_id=session.id,
                message_type="system",
                content=f"Error processing message: {str(e)}",
                created_at=datetime.utcnow()
            )
            self.db.add(error_message)
            self.db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing chat message"
            )

    def get_chat_history(self, session_token: str) -> List[Dict[str, Any]]:
        """Get chat history for a session."""
        session = self.db.query(DatasetChatSession).filter(
            DatasetChatSession.session_token == session_token
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at).all()
        
        return [
            {
                "id": msg.id,
                "type": msg.message_type,
                "content": msg.content,
                "metadata": msg.message_metadata,
                "tokens_used": msg.tokens_used,
                "processing_time_ms": msg.processing_time_ms,
                "created_at": msg.created_at
            }
            for msg in messages
        ]

    def end_chat_session(self, session_token: str) -> bool:
        """End a chat session."""
        session = self.db.query(DatasetChatSession).filter(
            DatasetChatSession.session_token == session_token
        ).first()
        
        if not session:
            return False
        
        session.is_active = False
        session.ended_at = datetime.utcnow()
        self.db.commit()
        
        return True

    def get_dataset_analytics(self, dataset_id: int, user_id: int) -> Dict[str, Any]:
        """Get analytics for a shared dataset."""
        dataset = self.db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.owner_id == user_id
        ).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # Get access statistics
        total_accesses = self.db.query(DatasetShareAccess).filter(
            DatasetShareAccess.dataset_id == dataset_id
        ).count()
        
        chat_sessions = self.db.query(DatasetChatSession).filter(
            DatasetChatSession.dataset_id == dataset_id
        ).count()
        
        total_messages = self.db.query(ChatMessage).join(DatasetChatSession).filter(
            DatasetChatSession.dataset_id == dataset_id
        ).count()
        
        return {
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "share_enabled": dataset.public_share_enabled,
            "view_count": dataset.share_view_count,
            "total_accesses": total_accesses,
            "chat_sessions": chat_sessions,
            "total_chat_messages": total_messages,
            "created_at": dataset.created_at,
            "last_accessed": dataset.last_accessed
        }

    def _generate_share_token(self, dataset_id: int, user_id: int) -> str:
        """Generate a unique share token."""
        data = f"{dataset_id}-{user_id}-{datetime.utcnow().isoformat()}-{secrets.token_hex(16)}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def _generate_session_token(self) -> str:
        """Generate a unique session token."""
        return secrets.token_urlsafe(32)

    def _log_share_access(
        self,
        dataset: Dataset,
        share_token: str,
        ip_address: Optional[str],
        user_agent: Optional[str]
    ):
        """Log access to a shared dataset."""
        access_log = DatasetShareAccess(
            dataset_id=dataset.id,
            share_token=share_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(access_log)
        self.db.commit()

    def _initialize_ai_context(self, dataset: Dataset):
        """Initialize AI context for dataset chat."""
        if not dataset.chat_context:
            context = {
                "dataset_name": dataset.name,
                "description": dataset.description,
                "type": dataset.type,
                "columns": dataset.schema_info.get("columns", []) if dataset.schema_info else [],
                "row_count": dataset.row_count,
                "summary": dataset.ai_summary
            }
            dataset.chat_context = context
            dataset.chat_model_name = settings.DEFAULT_GEMINI_MODEL
            self.db.commit()

    def _generate_system_prompt(self, dataset: Dataset) -> str:
        """Generate system prompt for AI chat."""
        prompt = f"""You are an AI assistant helping users understand and analyze the dataset "{dataset.name}".

Dataset Information:
- Name: {dataset.name}
- Description: {dataset.description or 'No description provided'}
- Type: {dataset.type}
- Rows: {dataset.row_count or 'Unknown'}
- Columns: {dataset.column_count or 'Unknown'}

"""
        
        if dataset.schema_info and "columns" in dataset.schema_info:
            prompt += "Dataset Schema:\n"
            for col in dataset.schema_info["columns"]:
                prompt += f"- {col.get('name', 'Unknown')}: {col.get('type', 'Unknown')}\n"
            prompt += "\n"
        
        if dataset.ai_summary:
            prompt += f"Dataset Summary: {dataset.ai_summary}\n\n"
        
        prompt += """You can help users:
1. Understand the dataset structure and content
2. Answer questions about the data
3. Suggest analysis approaches
4. Explain data patterns and insights
5. Help with data interpretation

Please provide helpful, accurate, and concise responses. If you're unsure about something, let the user know."""
        
        return prompt

    def _get_ai_response(
        self,
        dataset: Dataset,
        session: DatasetChatSession,
        user_message: str
    ) -> Dict[str, Any]:
        """Get AI response using MindsDB Gemini integration."""
        try:
            # Prepare context for AI
            context = f"""Dataset: {dataset.name}
User Question: {user_message}

Dataset Context: {dataset.chat_context}
"""
            
            # Use MindsDB service to get response
            response = self.mindsdb_service.ai_chat(
                message=context,
                model_name=session.ai_model_name
            )
            
            return {
                "content": response.get("answer", "I'm sorry, I couldn't process your request."),
                "metadata": response.get("metadata"),
                "tokens_used": response.get("tokens_used", 0)
            }
            
        except Exception as e:
            return {
                "content": f"I encountered an error while processing your request: {str(e)}",
                "metadata": {"error": True},
                "tokens_used": 0
            } 