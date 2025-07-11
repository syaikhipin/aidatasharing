from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class DatasetAccessLog(BaseModel):
    """Schema for dataset access log entry"""
    access_id: str
    dataset_id: int
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    access_type: str
    access_method: Optional[str] = None
    timestamp: datetime
    ip_address: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class DatasetDownloadLog(BaseModel):
    """Schema for dataset download log entry"""
    download_id: str
    dataset_id: int
    user_id: Optional[int] = None
    file_format: str
    download_method: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    success: bool = True
    file_size_bytes: Optional[int] = None
    
    class Config:
        from_attributes = True

class ChatInteractionLog(BaseModel):
    """Schema for chat interaction log entry"""
    interaction_id: str
    dataset_id: int
    user_id: Optional[int] = None
    user_message: str
    ai_response: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    tokens_used: Optional[int] = None
    response_time_seconds: Optional[float] = None
    timestamp: datetime
    success: bool = True
    
    class Config:
        from_attributes = True

class UsageStatsSummary(BaseModel):
    """Schema for aggregated usage statistics"""
    total_accesses: int = 0
    total_downloads: int = 0
    total_chats: int = 0
    total_api_calls: int = 0
    total_shares: int = 0
    unique_users: int = 0

class AccessByType(BaseModel):
    """Schema for access counts by type"""
    view: int = 0
    download: int = 0
    chat: int = 0
    share: int = 0
    api_call: int = 0

class DailyActivity(BaseModel):
    """Schema for daily activity data"""
    date: str
    count: int

class TopDataset(BaseModel):
    """Schema for top dataset information"""
    dataset_id: int
    name: str
    access_count: int

class TopUser(BaseModel):
    """Schema for top user information"""
    user_id: int
    username: str
    access_count: int

class RecentActivity(BaseModel):
    """Schema for recent activity entry"""
    access_id: str
    dataset_id: int
    access_type: str
    timestamp: str
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    success: bool = True

class AnalyticsPeriod(BaseModel):
    """Schema for analytics time period"""
    start_date: str
    end_date: str

class DatasetAnalyticsResponse(BaseModel):
    """Schema for dataset analytics response"""
    dataset_id: int
    period: AnalyticsPeriod
    summary: UsageStatsSummary
    access_by_type: Dict[str, int]
    daily_activity: List[DailyActivity]

class OrganizationAnalyticsResponse(BaseModel):
    """Schema for organization analytics response"""
    organization_id: int
    period: AnalyticsPeriod
    summary: UsageStatsSummary
    top_datasets: List[TopDataset]
    top_users: List[TopUser]

class DashboardOverviewResponse(BaseModel):
    """Schema for dashboard overview response"""
    last_24_hours: UsageStatsSummary
    last_7_days: Dict[str, int]
    top_datasets: List[TopDataset]
    recent_activity: List[RecentActivity]

class RealTimeActivityResponse(BaseModel):
    """Schema for real-time activity response"""
    activities: List[RecentActivity]
    total_count: int
    timestamp: str

class SystemMetric(BaseModel):
    """Schema for system metric entry"""
    timestamp: str
    cpu_usage_percent: Optional[float] = None
    memory_usage_percent: Optional[float] = None
    disk_usage_percent: Optional[float] = None
    total_datasets: Optional[int] = None
    total_users: Optional[int] = None
    total_organizations: Optional[int] = None
    mindsdb_health: Optional[str] = None

class SystemMetricsResponse(BaseModel):
    """Schema for system metrics response"""
    metrics: List[SystemMetric]
    period_hours: int
    total_records: int

class UsageStatsResponse(BaseModel):
    """Schema for usage statistics response"""
    date: str
    period_type: str
    dataset_id: Optional[int] = None
    organization_id: Optional[int] = None
    stats: UsageStatsSummary
    performance_metrics: Dict[str, float] = {}

class AnalyticsExportResponse(BaseModel):
    """Schema for analytics export response"""
    data: Any
    format: str
    dataset_id: Optional[int] = None
    organization_id: Optional[int] = None
    exported_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class LoggingResponse(BaseModel):
    """Schema for logging operation response"""
    status: str
    dataset_id: Optional[int] = None
    access_type: Optional[str] = None
    logged_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# Request schemas for logging endpoints
class DatasetAccessRequest(BaseModel):
    """Schema for dataset access logging request"""
    dataset_id: int
    access_type: str = Field(..., description="Type of access: 'view', 'download', 'chat', 'share', 'api_call'")
    session_id: Optional[str] = None
    access_method: str = "web"
    content_preview: Optional[str] = None
    query_text: Optional[str] = None

class DatasetDownloadRequest(BaseModel):
    """Schema for dataset download logging request"""
    dataset_id: int
    file_format: str
    download_method: str = Field(..., description="Method: 'direct', 'api', 'share_link'")
    file_size_bytes: Optional[int] = None
    success: bool = True
    share_token: Optional[str] = None

class ChatInteractionRequest(BaseModel):
    """Schema for chat interaction logging request"""
    dataset_id: int
    user_message: str
    ai_response: str
    session_id: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    tokens_used: Optional[int] = None
    response_time_seconds: Optional[float] = None
    success: bool = True

class APIUsageRequest(BaseModel):
    """Schema for API usage logging request"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    dataset_id: Optional[int] = None
    request_size_bytes: Optional[int] = None
    response_size_bytes: Optional[int] = None
    error_message: Optional[str] = None 