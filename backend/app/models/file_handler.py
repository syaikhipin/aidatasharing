"""
SQLAlchemy models for MindsDB file handler support
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class UploadStatus(str, enum.Enum):
    """File upload status"""
    PENDING = "pending"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingStatus(str, enum.Enum):
    """File processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class HandlerType(str, enum.Enum):
    """MindsDB handler types"""
    FILE = "file"
    DATABASE = "database"
    API = "api"
    ML_ENGINE = "ml_engine"
    IMAGE = "image"  # New image handler type


class FileType(str, enum.Enum):
    """File type classification"""
    DOCUMENT = "document"  # PDF, DOCX, TXT, etc.
    SPREADSHEET = "spreadsheet"  # CSV, XLSX, etc.
    IMAGE = "image"  # JPG, PNG, GIF, etc.
    ARCHIVE = "archive"  # ZIP, TAR, etc.
    OTHER = "other"


class FileUpload(Base):
    """File upload tracking table"""
    __tablename__ = "file_uploads"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # File information
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)
    mime_type = Column(String(100), nullable=True)
    file_type = Column(String(50), nullable=True)  # FileType enum value
    
    # Image-specific metadata
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    image_format = Column(String(10), nullable=True)  # JPEG, PNG, etc.
    color_mode = Column(String(20), nullable=True)  # RGB, RGBA, etc.
    
    # Processing status
    upload_status = Column(String(50), default=UploadStatus.PENDING)
    mindsdb_file_id = Column(String(255), nullable=True)
    mindsdb_storage_path = Column(String(500), nullable=True)  # For permanent storage path
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    file_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    dataset = relationship("Dataset")
    user = relationship("User")
    organization = relationship("Organization")
    processing_logs = relationship("FileProcessingLog", back_populates="file_upload")


class MindsDBHandler(Base):
    """MindsDB handler configuration table"""
    __tablename__ = "mindsdb_handlers"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Handler information
    handler_name = Column(String(100), nullable=False)
    handler_type = Column(String(50), nullable=False)
    configuration = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization")


class FileProcessingLog(Base):
    """File processing log table"""
    __tablename__ = "file_processing_logs"

    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"), nullable=False)
    
    # Log information
    step = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    message = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    file_upload = relationship("FileUpload", back_populates="processing_logs") 