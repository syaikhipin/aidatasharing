from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.models.organization import DataSharingLevel
from app.models.user import Base


class DatasetType(str, enum.Enum):
    """Types of datasets"""
    CSV = "csv"
    JSON = "json"
    DATABASE = "database"
    API = "api"
    S3_BUCKET = "s3_bucket"
    EXCEL = "excel"
    PARQUET = "parquet"
    PDF = "pdf"


class DatasetStatus(str, enum.Enum):
    """Dataset status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROCESSING = "processing"
    ERROR = "error"
    ARCHIVED = "archived"


class AIProcessingStatus(str, enum.Enum):
    """AI processing status for datasets"""
    NOT_PROCESSED = "not_processed"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    type = Column(Enum(DatasetType), nullable=False)
    status = Column(Enum(DatasetStatus), default=DatasetStatus.ACTIVE)
    
    # Data source information
    source_url = Column(String, nullable=True)  # File path, API endpoint, etc.
    connection_params = Column(JSON, nullable=True)  # Connection parameters
    
    # Organization and sharing - ORGANIZATION IS REQUIRED (no cross-org sharing)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)  # Required!
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    sharing_level = Column(Enum(DataSharingLevel), default=DataSharingLevel.PRIVATE)
    
    # Metadata
    size_bytes = Column(Integer, nullable=True)
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    schema_info = Column(JSON, nullable=True)  # Schema/column information
    
    # MindsDB integration
    mindsdb_table_name = Column(String, nullable=True)  # Name in MindsDB
    mindsdb_database = Column(String, nullable=True)  # MindsDB database name
    
    # AI Processing Status
    ai_processing_status = Column(Enum(AIProcessingStatus), default=AIProcessingStatus.NOT_PROCESSED)
    ai_summary = Column(Text, nullable=True)  # AI-generated summary
    ai_insights = Column(JSON, nullable=True)  # AI-generated insights
    ai_recommendations = Column(JSON, nullable=True)  # AI recommendations
    
    # Data Sharing Features
    public_share_enabled = Column(Boolean, default=False)
    share_token = Column(String, nullable=True, unique=True)  # For public sharing
    share_expires_at = Column(DateTime, nullable=True)
    share_password = Column(String, nullable=True)  # Optional password protection
    share_view_count = Column(Integer, default=0)
    
    # AI Chat Features
    ai_chat_enabled = Column(Boolean, default=True)
    chat_model_name = Column(String, nullable=True)  # Gemini model used for chat
    chat_context = Column(JSON, nullable=True)  # Context for AI chat
    
    # Access control within organization
    allow_download = Column(Boolean, default=True)
    allow_api_access = Column(Boolean, default=True)
    allow_ai_chat = Column(Boolean, default=True)
    allow_model_training = Column(Boolean, default=True)
    
    # Data Quality Metrics (AI-powered)
    data_quality_score = Column(String, nullable=True)  # Overall quality score
    completeness_score = Column(String, nullable=True)
    consistency_score = Column(String, nullable=True)
    accuracy_score = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=True)
    ai_processed_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="owned_datasets")
    organization = relationship("Organization")
    department = relationship("Department")
    access_logs = relationship("DatasetAccessLog", back_populates="dataset")
    models = relationship("DatasetModel", back_populates="dataset")
    chat_sessions = relationship("DatasetChatSession", back_populates="dataset")
    share_accesses = relationship("DatasetShareAccess", back_populates="dataset")


class DatasetAccessLog(Base):
    __tablename__ = "dataset_access_logs"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Can be null for public access
    access_type = Column(String, nullable=False)  # 'view', 'download', 'api', 'query', 'chat'
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    share_token = Column(String, nullable=True)  # If accessed via share link
    session_id = Column(String, nullable=True)  # For tracking anonymous sessions
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    dataset = relationship("Dataset", back_populates="access_logs")
    user = relationship("User")


class DatasetModel(Base):
    __tablename__ = "dataset_models"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    name = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # 'predictor', 'classifier', 'chat', 'embedding'
    mindsdb_model_name = Column(String, nullable=False)
    
    # Model configuration
    target_column = Column(String, nullable=True)
    feature_columns = Column(JSON, nullable=True)
    model_params = Column(JSON, nullable=True)
    
    # AI Engine Information
    engine_type = Column(String, nullable=True)  # 'gemini', 'lightgbm', 'neural_network'
    ai_model_version = Column(String, nullable=True)  # e.g., 'gemini-2.0-flash'
    
    # Performance metrics
    accuracy = Column(String, nullable=True)
    training_time = Column(Integer, nullable=True)  # seconds
    prediction_count = Column(Integer, default=0)
    last_prediction_at = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String, default="training")  # 'training', 'complete', 'error', 'archived'
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    dataset = relationship("Dataset", back_populates="models")


class DatasetChatSession(Base):
    __tablename__ = "dataset_chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Can be null for public access
    session_token = Column(String, nullable=False, unique=True)
    share_token = Column(String, nullable=True)  # If accessed via share link
    
    # Session metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Chat configuration
    ai_model_name = Column(String, nullable=False)  # e.g., 'gemini-2.0-flash'
    system_prompt = Column(Text, nullable=True)
    context_data = Column(JSON, nullable=True)  # Dataset context for AI
    
    # Session stats
    message_count = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    ended_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    dataset = relationship("Dataset", back_populates="chat_sessions")
    user = relationship("User")
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("dataset_chat_sessions.id"), nullable=False)
    
    # Message content
    message_type = Column(String, nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, nullable=True)  # Additional message metadata (renamed from metadata)
    
    # AI processing info
    tokens_used = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    ai_model_version = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("DatasetChatSession", back_populates="messages")


class DatasetShareAccess(Base):
    __tablename__ = "dataset_share_accesses"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    share_token = Column(String, nullable=False)
    
    # Access details
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    referrer = Column(String, nullable=True)
    
    # Geographic info (optional)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    
    # Access metadata
    access_duration_seconds = Column(Integer, nullable=True)
    pages_viewed = Column(Integer, default=1)
    files_downloaded = Column(Integer, default=0)
    chat_messages_sent = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    dataset = relationship("Dataset", back_populates="share_accesses")


# Add to User model relationship
# Note: This would need to be added to the User model in user.py
# owned_datasets = relationship("Dataset", back_populates="owner") 