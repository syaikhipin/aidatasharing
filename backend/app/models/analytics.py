from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, JSON, Float, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.core.database import Base


class ActivityType(str, enum.Enum):
    """Types of user activities to track"""
    LOGIN = "login"
    LOGOUT = "logout"
    DATASET_VIEW = "dataset_view"
    DATASET_UPLOAD = "dataset_upload"
    DATASET_DOWNLOAD = "dataset_download"
    MODEL_CREATE = "model_create"
    MODEL_TRAIN = "model_train"
    MODEL_PREDICT = "model_predict"
    SQL_QUERY = "sql_query"
    API_CALL = "api_call"
    ADMIN_ACTION = "admin_action"
    ORG_JOIN = "org_join"
    ORG_LEAVE = "org_leave"


class UsageMetricType(str, enum.Enum):
    """Types of usage metrics"""
    STORAGE_BYTES = "storage_bytes"
    API_CALLS = "api_calls"
    MODEL_PREDICTIONS = "model_predictions"
    SQL_QUERIES = "sql_queries"
    ACTIVE_USERS = "active_users"
    DATASET_DOWNLOADS = "dataset_downloads"


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    activity_type = Column(Enum(ActivityType), nullable=False)
    
    # Activity details
    resource_id = Column(Integer, nullable=True)  # ID of dataset, model, etc.
    resource_type = Column(String, nullable=True)  # 'dataset', 'model', etc.
    description = Column(Text, nullable=True)
    meta_data = Column(JSON, nullable=True)  # Additional context
    
    # Request details
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    endpoint = Column(String, nullable=True)
    method = Column(String, nullable=True)
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User")
    organization = relationship("Organization")


class UsageMetric(Base):
    __tablename__ = "usage_metrics"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    metric_type = Column(Enum(UsageMetricType), nullable=False)
    
    # Metric values
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)  # 'bytes', 'count', etc.
    
    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    granularity = Column(String, default="daily")  # 'hourly', 'daily', 'monthly'
    
    # Metadata
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")
    organization = relationship("Organization")


class DatashareStats(Base):
    __tablename__ = "datashare_stats"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Dataset statistics
    total_datasets = Column(Integer, default=0)
    private_datasets = Column(Integer, default=0)
    department_datasets = Column(Integer, default=0)
    organization_datasets = Column(Integer, default=0)
    
    # Storage statistics
    total_storage_bytes = Column(Integer, default=0)
    avg_dataset_size_bytes = Column(Integer, default=0)
    
    # Usage statistics
    total_downloads = Column(Integer, default=0)
    total_api_calls = Column(Integer, default=0)
    active_users_count = Column(Integer, default=0)
    
    # Model statistics
    total_models = Column(Integer, default=0)
    active_models = Column(Integer, default=0)
    total_predictions = Column(Integer, default=0)
    
    # Period
    stats_date = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    organization = relationship("Organization")


class UserSessionLog(Base):
    __tablename__ = "user_session_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Session details
    session_token = Column(String, nullable=False, index=True)
    login_time = Column(DateTime, default=datetime.utcnow)
    logout_time = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Session metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    login_method = Column(String, default="password")  # 'password', 'sso', etc.
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    organization = relationship("Organization")


class ModelPerformanceLog(Base):
    __tablename__ = "model_performance_logs"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("dataset_models.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Performance metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    
    # Execution metrics
    prediction_time_ms = Column(Float, nullable=True)
    training_time_seconds = Column(Integer, nullable=True)
    data_rows_processed = Column(Integer, nullable=True)
    
    # Metadata
    evaluation_type = Column(String, nullable=True)  # 'training', 'validation', 'production'
    meta_data = Column(JSON, nullable=True)
    
    # Timestamps
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    model = relationship("DatasetModel")
    organization = relationship("Organization")


class DatasetAccess(Base):
    """Track dataset access and interaction events"""
    __tablename__ = "dataset_access"
    
    id = Column(Integer, primary_key=True, index=True)
    access_id = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # What was accessed
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for anonymous access
    session_id = Column(String, nullable=True)  # For anonymous sessions
    
    # Access details
    access_type = Column(String, nullable=False)  # 'view', 'download', 'chat', 'share', 'api_call'
    access_method = Column(String, nullable=True)  # 'web', 'api', 'public_link', 'direct'
    
    # Technical details
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    referer = Column(String, nullable=True)
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_seconds = Column(Float, nullable=True)  # How long the session lasted
    
    # Content details
    content_preview = Column(Text, nullable=True)  # What content was accessed
    query_text = Column(Text, nullable=True)  # For chat interactions
    
    # Context
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    
    # Success/Error tracking
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    dataset = relationship("Dataset")
    user = relationship("User")
    organization = relationship("Organization")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_dataset_access_timestamp', 'dataset_id', 'timestamp'),
        Index('idx_dataset_access_type', 'access_type', 'timestamp'),
        Index('idx_dataset_access_user', 'user_id', 'timestamp'),
        Index('idx_dataset_access_org', 'organization_id', 'timestamp'),
    )


# DatasetDownload class is defined in app.models.dataset to avoid table conflicts
from app.models.dataset import DatasetDownload


class ChatInteraction(Base):
    """Track AI chat interactions with datasets"""
    __tablename__ = "chat_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # What was chatted with
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String, nullable=True)
    
    # Chat details
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=True)
    llm_provider = Column(String, nullable=True)  # 'gemini', 'openai', etc.
    llm_model = Column(String, nullable=True)     # 'gemini-pro', 'gpt-4', etc.
    
    # Technical metrics
    tokens_used = Column(Integer, nullable=True)
    response_time_seconds = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Context
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Success tracking
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    dataset = relationship("Dataset")
    user = relationship("User")
    organization = relationship("Organization")


class APIUsage(Base):
    """Track API endpoint usage and performance"""
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Request details
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)  # GET, POST, PUT, DELETE
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Technical details
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Performance metrics
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    response_time_ms = Column(Float, nullable=True)
    status_code = Column(Integer, nullable=True)
    
    # Resource usage
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Request/Response details
    request_size_bytes = Column(Integer, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User")
    dataset = relationship("Dataset")
    organization = relationship("Organization")


class UsageStats(Base):
    """Aggregated usage statistics for efficient dashboard queries"""
    __tablename__ = "usage_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Aggregation period
    date = Column(DateTime, nullable=False)
    period_type = Column(String, nullable=False)  # 'hour', 'day', 'week', 'month'
    
    # What the stats are about
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Aggregated metrics
    total_views = Column(Integer, default=0)
    total_downloads = Column(Integer, default=0)
    total_chats = Column(Integer, default=0)
    total_api_calls = Column(Integer, default=0)
    total_shares = Column(Integer, default=0)
    
    # Performance metrics
    avg_response_time_ms = Column(Float, nullable=True)
    total_tokens_used = Column(Integer, default=0)
    total_bytes_transferred = Column(Integer, default=0)
    
    # User engagement
    unique_users = Column(Integer, default=0)
    unique_sessions = Column(Integer, default=0)
    avg_session_duration = Column(Float, nullable=True)
    
    # Success rates
    success_rate = Column(Float, nullable=True)  # Percentage
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dataset = relationship("Dataset")
    user = relationship("User")
    organization = relationship("Organization")
    
    # Indexes for efficient aggregation queries
    __table_args__ = (
        Index('idx_usage_stats_date_period', 'date', 'period_type'),
        Index('idx_usage_stats_dataset_date', 'dataset_id', 'date'),
        Index('idx_usage_stats_org_date', 'organization_id', 'date'),
    )


class SystemMetrics(Base):
    """Track overall system performance and health metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # System performance
    cpu_usage_percent = Column(Float, nullable=True)
    memory_usage_percent = Column(Float, nullable=True)
    disk_usage_percent = Column(Float, nullable=True)
    
    # Database metrics
    active_connections = Column(Integer, nullable=True)
    total_datasets = Column(Integer, nullable=True)
    total_users = Column(Integer, nullable=True)
    total_organizations = Column(Integer, nullable=True)
    
    # Application metrics
    active_sessions = Column(Integer, nullable=True)
    requests_per_minute = Column(Float, nullable=True)
    avg_response_time_ms = Column(Float, nullable=True)
    
    # Storage metrics
    total_storage_bytes = Column(Integer, nullable=True)
    available_storage_bytes = Column(Integer, nullable=True)
    
    # MindsDB metrics
    mindsdb_health = Column(String, nullable=True)  # 'healthy', 'degraded', 'error'
    mindsdb_response_time_ms = Column(Float, nullable=True) 