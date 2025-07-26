"""
Enhanced Configuration Models for Admin Panel
Supports environment variable overrides and MindsDB configuration management
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Enum
from datetime import datetime
import enum
from app.core.database import Base


class ConfigCategory(str, enum.Enum):
    """Configuration categories"""
    SYSTEM = "system"
    DATABASE = "database"
    MINDSDB = "mindsdb"
    AI_MODELS = "ai_models"
    FILE_UPLOAD = "file_upload"
    SECURITY = "security"
    CORS = "cors"
    AWS = "aws"
    DATA_SHARING = "data_sharing"
    DOCUMENT_PROCESSING = "document_processing"
    DATA_CONNECTORS = "data_connectors"


class ConfigType(str, enum.Enum):
    """Configuration value types"""
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    JSON = "json"
    LIST = "list"
    PASSWORD = "password"
    URL = "url"
    EMAIL = "email"


class ConfigurationOverride(Base):
    """Enhanced configuration table with environment variable override support"""
    __tablename__ = "configuration_overrides"

    id = Column(Integer, primary_key=True, index=True)
    
    # Configuration identification
    key = Column(String(255), unique=True, index=True, nullable=False)
    category = Column(String(50), nullable=False, default=ConfigCategory.SYSTEM)
    config_type = Column(String(50), nullable=False, default=ConfigType.STRING)
    
    # Values
    value = Column(Text, nullable=True)
    default_value = Column(Text, nullable=True)
    env_var_name = Column(String(255), nullable=True)  # Environment variable name
    
    # Metadata
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_sensitive = Column(Boolean, default=False)  # For passwords, API keys
    is_required = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    requires_restart = Column(Boolean, default=False)  # If change requires app restart
    
    # Validation
    validation_regex = Column(String(500), nullable=True)
    min_value = Column(Integer, nullable=True)
    max_value = Column(Integer, nullable=True)
    allowed_values = Column(JSON, nullable=True)  # For enum-like values
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_applied_at = Column(DateTime, nullable=True)


class MindsDBConfiguration(Base):
    """MindsDB-specific configuration management"""
    __tablename__ = "mindsdb_configurations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Configuration identification
    config_name = Column(String(100), nullable=False)  # e.g., "main", "backup"
    is_active = Column(Boolean, default=True)
    
    # MindsDB connection settings
    mindsdb_url = Column(String(500), nullable=False)
    mindsdb_database = Column(String(100), default="mindsdb")
    mindsdb_username = Column(String(100), nullable=True)
    mindsdb_password = Column(String(255), nullable=True)
    
    # Permanent storage configuration
    permanent_storage_config = Column(JSON, nullable=True)
    
    # AI engine configurations
    ai_engines_config = Column(JSON, nullable=True)
    
    # File upload settings
    file_upload_config = Column(JSON, nullable=True)
    
    # Custom MindsDB settings
    custom_config = Column(JSON, nullable=True)
    
    # Health and status
    last_health_check = Column(DateTime, nullable=True)
    is_healthy = Column(Boolean, default=False)
    health_status = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConfigurationHistory(Base):
    """Track configuration changes for audit purposes"""
    __tablename__ = "configuration_history"

    id = Column(Integer, primary_key=True, index=True)
    
    # Reference to configuration
    config_key = Column(String(255), nullable=False)
    config_type = Column(String(50), nullable=False)  # 'override' or 'mindsdb'
    
    # Change details
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    change_reason = Column(Text, nullable=True)
    
    # User who made the change
    changed_by_user_id = Column(Integer, nullable=True)
    changed_by_email = Column(String(255), nullable=True)
    
    # Timestamps
    changed_at = Column(DateTime, default=datetime.utcnow)
    
    # Application status
    applied_successfully = Column(Boolean, nullable=True)
    application_error = Column(Text, nullable=True)
    applied_at = Column(DateTime, nullable=True)