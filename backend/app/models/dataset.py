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


class DatasetStatus(str, enum.Enum):
    """Dataset status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROCESSING = "processing"
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
    
    # Access control within organization
    allow_download = Column(Boolean, default=True)
    allow_api_access = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="owned_datasets")
    organization = relationship("Organization")
    department = relationship("Department")
    access_logs = relationship("DatasetAccessLog", back_populates="dataset")
    models = relationship("DatasetModel", back_populates="dataset")


class DatasetAccessLog(Base):
    __tablename__ = "dataset_access_logs"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    access_type = Column(String, nullable=False)  # 'view', 'download', 'api', 'query'
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    dataset = relationship("Dataset", back_populates="access_logs")
    user = relationship("User")


class DatasetModel(Base):
    __tablename__ = "dataset_models"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    name = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # 'predictor', 'classifier', etc.
    mindsdb_model_name = Column(String, nullable=False)
    
    # Model configuration
    target_column = Column(String, nullable=True)
    feature_columns = Column(JSON, nullable=True)
    model_params = Column(JSON, nullable=True)
    
    # Performance metrics
    accuracy = Column(String, nullable=True)
    training_time = Column(Integer, nullable=True)  # seconds
    
    # Status
    status = Column(String, default="training")  # 'training', 'complete', 'error'
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    dataset = relationship("Dataset", back_populates="models")


# Add to User model relationship
# Note: This would need to be added to the User model in user.py
# owned_datasets = relationship("Dataset", back_populates="owner") 