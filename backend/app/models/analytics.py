from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.models.user import Base


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