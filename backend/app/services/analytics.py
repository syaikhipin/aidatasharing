from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import asyncio
from fastapi import Request
import psutil
import logging
import json

from app.core.database import get_db
from app.models.analytics import (
    DatasetAccess, ChatInteraction, 
    APIUsage, UsageStats, SystemMetrics
)
from app.models.dataset import DatasetDownload
from app.models.dataset import Dataset
from app.models.user import User
from app.models.organization import Organization

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for comprehensive data logging and analytics"""
    
    def __init__(self):
        self.db_session = None
    
    def get_session(self) -> Session:
        """Get database session"""
        if not self.db_session:
            self.db_session = next(get_db())
        return self.db_session
    
    async def log_dataset_access(
        self,
        dataset_id: int,
        access_type: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        request: Optional[Request] = None,
        **kwargs
    ) -> str:
        """
        Log dataset access event
        
        Args:
            dataset_id: ID of the dataset accessed
            access_type: Type of access ('view', 'download', 'chat', 'share', 'api_call')
            user_id: User ID (None for anonymous)
            session_id: Session ID for anonymous users
            request: FastAPI request object for extracting metadata
            **kwargs: Additional context data
        
        Returns:
            access_id: Unique identifier for this access event
        """
        try:
            db = self.get_session()
            
            # Extract technical details from request
            ip_address = None
            user_agent = None
            referer = None
            
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                referer = request.headers.get("referer")
            
            access_log = DatasetAccess(
                dataset_id=dataset_id,
                user_id=user_id,
                session_id=session_id,
                access_type=access_type,
                access_method=kwargs.get('access_method', 'web'),
                ip_address=ip_address,
                user_agent=user_agent,
                referer=referer,
                content_preview=kwargs.get('content_preview'),
                query_text=kwargs.get('query_text'),
                organization_id=kwargs.get('organization_id'),
                department_id=kwargs.get('department_id'),
                success=kwargs.get('success', True),
                error_message=kwargs.get('error_message'),
                duration_seconds=kwargs.get('duration_seconds')
            )
            
            db.add(access_log)
            db.commit()
            db.refresh(access_log)
            
            # Trigger background aggregation update
            asyncio.create_task(self._update_usage_stats(
                dataset_id=dataset_id,
                user_id=user_id,
                organization_id=kwargs.get('organization_id'),
                access_type=access_type
            ))
            
            return access_log.access_id
            
        except Exception as e:
            logger.error(f"Error logging dataset access: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            return None
    
    async def log_dataset_download(
        self,
        dataset_id: int,
        file_format: str,
        download_method: str,
        user_id: Optional[int] = None,
        request: Optional[Request] = None,
        **kwargs
    ) -> str:
        """Log dataset download event"""
        try:
            db = self.get_session()
            
            ip_address = None
            user_agent = None
            
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
            
            download_log = DatasetDownload(
                dataset_id=dataset_id,
                user_id=user_id,
                file_format=file_format,
                download_method=download_method,
                ip_address=ip_address,
                user_agent=user_agent,
                file_size_bytes=kwargs.get('file_size_bytes'),
                completed_at=kwargs.get('completed_at'),
                duration_seconds=kwargs.get('duration_seconds'),
                success=kwargs.get('success', True),
                bytes_transferred=kwargs.get('bytes_transferred'),
                error_message=kwargs.get('error_message'),
                organization_id=kwargs.get('organization_id'),
                share_token=kwargs.get('share_token')
            )
            
            db.add(download_log)
            db.commit()
            db.refresh(download_log)
            
            # Also log as general access
            await self.log_dataset_access(
                dataset_id=dataset_id,
                access_type='download',
                user_id=user_id,
                request=request,
                organization_id=kwargs.get('organization_id')
            )
            
            return download_log.download_id
            
        except Exception as e:
            logger.error(f"Error logging dataset download: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            return None
    
    async def log_chat_interaction(
        self,
        dataset_id: int,
        user_message: str,
        ai_response: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        request: Optional[Request] = None,
        **kwargs
    ) -> str:
        """Log AI chat interaction"""
        try:
            db = self.get_session()
            
            ip_address = None
            user_agent = None
            
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
            
            chat_log = ChatInteraction(
                dataset_id=dataset_id,
                user_id=user_id,
                session_id=session_id,
                user_message=user_message,
                ai_response=ai_response,
                llm_provider=kwargs.get('llm_provider'),
                llm_model=kwargs.get('llm_model'),
                tokens_used=kwargs.get('tokens_used'),
                response_time_seconds=kwargs.get('response_time_seconds'),
                ip_address=ip_address,
                user_agent=user_agent,
                organization_id=kwargs.get('organization_id'),
                success=kwargs.get('success', True),
                error_message=kwargs.get('error_message')
            )
            
            db.add(chat_log)
            db.commit()
            db.refresh(chat_log)
            
            # Also log as general access
            await self.log_dataset_access(
                dataset_id=dataset_id,
                access_type='chat',
                user_id=user_id,
                session_id=session_id,
                request=request,
                query_text=user_message,
                organization_id=kwargs.get('organization_id')
            )
            
            return chat_log.interaction_id
            
        except Exception as e:
            logger.error(f"Error logging chat interaction: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            return None
    
    async def log_api_usage(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        user_id: Optional[int] = None,
        request: Optional[Request] = None,
        **kwargs
    ) -> str:
        """Log API endpoint usage"""
        try:
            db = self.get_session()
            
            ip_address = None
            user_agent = None
            
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
            
            api_log = APIUsage(
                endpoint=endpoint,
                method=method,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                response_time_ms=response_time_ms,
                status_code=status_code,
                dataset_id=kwargs.get('dataset_id'),
                organization_id=kwargs.get('organization_id'),
                request_size_bytes=kwargs.get('request_size_bytes'),
                response_size_bytes=kwargs.get('response_size_bytes'),
                error_message=kwargs.get('error_message')
            )
            
            db.add(api_log)
            db.commit()
            db.refresh(api_log)
            
            return api_log.request_id
            
        except Exception as e:
            logger.error(f"Error logging API usage: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            return None
    
    async def _update_usage_stats(
        self,
        dataset_id: Optional[int] = None,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        access_type: Optional[str] = None
    ):
        """Update aggregated usage statistics"""
        try:
            db = self.get_session()
            
            # Update hourly stats
            current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            
            # Find or create usage stats record
            stats = db.query(UsageStats).filter(
                and_(
                    UsageStats.date == current_hour,
                    UsageStats.period_type == 'hour',
                    UsageStats.dataset_id == dataset_id,
                    UsageStats.organization_id == organization_id
                )
            ).first()
            
            if not stats:
                stats = UsageStats(
                    date=current_hour,
                    period_type='hour',
                    dataset_id=dataset_id,
                    user_id=user_id,
                    organization_id=organization_id
                )
                db.add(stats)
            
            # Update counters based on access type
            if access_type == 'view':
                stats.total_views += 1
            elif access_type == 'download':
                stats.total_downloads += 1
            elif access_type == 'chat':
                stats.total_chats += 1
            elif access_type == 'api_call':
                stats.total_api_calls += 1
            elif access_type == 'share':
                stats.total_shares += 1
            
            stats.updated_at = datetime.utcnow()
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating usage stats: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
    
    async def get_dataset_analytics(
        self,
        dataset_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        organization_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get comprehensive analytics for a specific dataset"""
        try:
            db = self.get_session()
            
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Basic access metrics
            access_query = db.query(DatasetAccess).filter(
                and_(
                    DatasetAccess.dataset_id == dataset_id,
                    DatasetAccess.timestamp >= start_date,
                    DatasetAccess.timestamp <= end_date
                )
            )
            
            if organization_id:
                access_query = access_query.filter(DatasetAccess.organization_id == organization_id)
            
            total_accesses = access_query.count()
            
            # Access by type
            access_by_type = db.query(
                DatasetAccess.access_type,
                func.count(DatasetAccess.id).label('count')
            ).filter(
                and_(
                    DatasetAccess.dataset_id == dataset_id,
                    DatasetAccess.timestamp >= start_date,
                    DatasetAccess.timestamp <= end_date
                )
            ).group_by(DatasetAccess.access_type).all()
            
            # Downloads
            downloads = db.query(DatasetDownload).filter(
                and_(
                    DatasetDownload.dataset_id == dataset_id,
                    DatasetDownload.started_at >= start_date,
                    DatasetDownload.started_at <= end_date
                )
            ).count()
            
            # Chat interactions
            chats = db.query(ChatInteraction).filter(
                and_(
                    ChatInteraction.dataset_id == dataset_id,
                    ChatInteraction.timestamp >= start_date,
                    ChatInteraction.timestamp <= end_date
                )
            ).count()
            
            # Unique users
            unique_users = db.query(func.count(func.distinct(DatasetAccess.user_id))).filter(
                and_(
                    DatasetAccess.dataset_id == dataset_id,
                    DatasetAccess.timestamp >= start_date,
                    DatasetAccess.timestamp <= end_date,
                    DatasetAccess.user_id.isnot(None)
                )
            ).scalar()
            
            # Daily activity
            daily_activity = db.query(
                func.date(DatasetAccess.timestamp).label('date'),
                func.count(DatasetAccess.id).label('count')
            ).filter(
                and_(
                    DatasetAccess.dataset_id == dataset_id,
                    DatasetAccess.timestamp >= start_date,
                    DatasetAccess.timestamp <= end_date
                )
            ).group_by(func.date(DatasetAccess.timestamp)).all()
            
            return {
                "dataset_id": dataset_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "summary": {
                    "total_accesses": total_accesses,
                    "total_downloads": downloads,
                    "total_chats": chats,
                    "unique_users": unique_users or 0
                },
                "access_by_type": {row.access_type: row.count for row in access_by_type},
                "daily_activity": [
                    {"date": row.date.isoformat(), "count": row.count}
                    for row in daily_activity
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting dataset analytics: {str(e)}")
            return {"error": str(e)}
    
    async def get_organization_analytics(
        self,
        organization_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive analytics for an organization"""
        try:
            db = self.get_session()
            
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Most accessed datasets
            top_datasets = db.query(
                DatasetAccess.dataset_id,
                func.count(DatasetAccess.id).label('access_count'),
                Dataset.name
            ).join(Dataset).filter(
                and_(
                    DatasetAccess.organization_id == organization_id,
                    DatasetAccess.timestamp >= start_date,
                    DatasetAccess.timestamp <= end_date
                )
            ).group_by(DatasetAccess.dataset_id, Dataset.name).order_by(
                func.count(DatasetAccess.id).desc()
            ).limit(10).all()
            
            # User activity
            user_activity = db.query(
                DatasetAccess.user_id,
                func.count(DatasetAccess.id).label('access_count'),
                User.username
            ).join(User, DatasetAccess.user_id == User.id).filter(
                and_(
                    DatasetAccess.organization_id == organization_id,
                    DatasetAccess.timestamp >= start_date,
                    DatasetAccess.timestamp <= end_date
                )
            ).group_by(DatasetAccess.user_id, User.username).order_by(
                func.count(DatasetAccess.id).desc()
            ).limit(10).all()
            
            # Total metrics
            total_accesses = db.query(DatasetAccess).filter(
                and_(
                    DatasetAccess.organization_id == organization_id,
                    DatasetAccess.timestamp >= start_date,
                    DatasetAccess.timestamp <= end_date
                )
            ).count()
            
            total_downloads = db.query(DatasetDownload).filter(
                and_(
                    DatasetDownload.organization_id == organization_id,
                    DatasetDownload.started_at >= start_date,
                    DatasetDownload.started_at <= end_date
                )
            ).count()
            
            total_chats = db.query(ChatInteraction).filter(
                and_(
                    ChatInteraction.organization_id == organization_id,
                    ChatInteraction.timestamp >= start_date,
                    ChatInteraction.timestamp <= end_date
                )
            ).count()
            
            return {
                "organization_id": organization_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "summary": {
                    "total_accesses": total_accesses,
                    "total_downloads": total_downloads,
                    "total_chats": total_chats
                },
                "top_datasets": [
                    {
                        "dataset_id": row.dataset_id,
                        "name": row.name,
                        "access_count": row.access_count
                    }
                    for row in top_datasets
                ],
                "top_users": [
                    {
                        "user_id": row.user_id,
                        "username": row.username,
                        "access_count": row.access_count
                    }
                    for row in user_activity
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting organization analytics: {str(e)}")
            return {"error": str(e)}
    
    async def record_system_metrics(self):
        """Record current system performance metrics"""
        try:
            db = self.get_session()
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Database metrics
            total_datasets = db.query(Dataset).count()
            total_users = db.query(User).count()
            total_orgs = db.query(Organization).count()
            
            # Create system metrics record
            metrics = SystemMetrics(
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory.percent,
                disk_usage_percent=disk.percent,
                total_datasets=total_datasets,
                total_users=total_users,
                total_organizations=total_orgs
            )
            
            db.add(metrics)
            db.commit()
            
            logger.info(f"Recorded system metrics: CPU {cpu_percent}%, Memory {memory.percent}%")
            
        except Exception as e:
            logger.error(f"Error recording system metrics: {str(e)}")
            if self.db_session:
                self.db_session.rollback()

# Global analytics service instance
analytics_service = AnalyticsService() 