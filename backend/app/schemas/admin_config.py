"""
Enhanced Configuration Schemas for Admin Panel
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum


class ConfigCategoryEnum(str, Enum):
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


class ConfigTypeEnum(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    JSON = "json"
    LIST = "list"
    PASSWORD = "password"
    URL = "url"
    EMAIL = "email"


# Configuration Override Schemas
class ConfigurationOverrideBase(BaseModel):
    key: str = Field(..., description="Configuration key")
    category: ConfigCategoryEnum = Field(default=ConfigCategoryEnum.SYSTEM)
    config_type: ConfigTypeEnum = Field(default=ConfigTypeEnum.STRING)
    value: Optional[str] = Field(None, description="Current value")
    default_value: Optional[str] = Field(None, description="Default value")
    env_var_name: Optional[str] = Field(None, description="Environment variable name")
    title: str = Field(..., description="Human-readable title")
    description: Optional[str] = Field(None, description="Configuration description")
    is_sensitive: bool = Field(default=False, description="Is this a sensitive value?")
    is_required: bool = Field(default=False, description="Is this configuration required?")
    is_active: bool = Field(default=True, description="Is this configuration active?")
    requires_restart: bool = Field(default=False, description="Does changing this require restart?")
    validation_regex: Optional[str] = Field(None, description="Validation regex pattern")
    min_value: Optional[int] = Field(None, description="Minimum value for integers")
    max_value: Optional[int] = Field(None, description="Maximum value for integers")
    allowed_values: Optional[List[str]] = Field(None, description="Allowed values for enums")


class ConfigurationOverrideCreate(ConfigurationOverrideBase):
    pass


class ConfigurationOverrideUpdate(BaseModel):
    value: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    validation_regex: Optional[str] = None
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    allowed_values: Optional[List[str]] = None


class ConfigurationOverride(ConfigurationOverrideBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_applied_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# MindsDB Configuration Schemas
class MindsDBConfigurationBase(BaseModel):
    config_name: str = Field(..., description="Configuration name")
    is_active: bool = Field(default=True)
    mindsdb_url: str = Field(..., description="MindsDB URL")
    mindsdb_database: str = Field(default="mindsdb")
    mindsdb_username: Optional[str] = None
    mindsdb_password: Optional[str] = None
    permanent_storage_config: Optional[Dict[str, Any]] = None
    ai_engines_config: Optional[Dict[str, Any]] = None
    file_upload_config: Optional[Dict[str, Any]] = None
    custom_config: Optional[Dict[str, Any]] = None


class MindsDBConfigurationCreate(MindsDBConfigurationBase):
    pass


class MindsDBConfigurationUpdate(BaseModel):
    config_name: Optional[str] = None
    is_active: Optional[bool] = None
    mindsdb_url: Optional[str] = None
    mindsdb_database: Optional[str] = None
    mindsdb_username: Optional[str] = None
    mindsdb_password: Optional[str] = None
    permanent_storage_config: Optional[Dict[str, Any]] = None
    ai_engines_config: Optional[Dict[str, Any]] = None
    file_upload_config: Optional[Dict[str, Any]] = None
    custom_config: Optional[Dict[str, Any]] = None


class MindsDBConfiguration(MindsDBConfigurationBase):
    id: int
    last_health_check: Optional[datetime] = None
    is_healthy: bool = False
    health_status: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Configuration History Schemas
class ConfigurationHistoryBase(BaseModel):
    config_key: str
    config_type: str  # 'override' or 'mindsdb'
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    change_reason: Optional[str] = None


class ConfigurationHistoryCreate(ConfigurationHistoryBase):
    changed_by_user_id: Optional[int] = None
    changed_by_email: Optional[str] = None


class ConfigurationHistory(ConfigurationHistoryBase):
    id: int
    changed_by_user_id: Optional[int] = None
    changed_by_email: Optional[str] = None
    changed_at: datetime
    applied_successfully: Optional[bool] = None
    application_error: Optional[str] = None
    applied_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Combined Configuration Response
class SystemConfiguration(BaseModel):
    """Complete system configuration including overrides and MindsDB config"""
    environment_overrides: List[ConfigurationOverride]
    mindsdb_configurations: List[MindsDBConfiguration]
    active_mindsdb_config: Optional[MindsDBConfiguration] = None
    system_info: Dict[str, Any]
    restart_required: bool = False


# Configuration validation and application
class ConfigurationValidationResult(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []


class ConfigurationApplicationResult(BaseModel):
    success: bool
    applied_configs: List[str] = []
    failed_configs: List[str] = []
    errors: List[str] = []
    restart_required: bool = False


# Bulk configuration operations
class BulkConfigurationUpdate(BaseModel):
    overrides: List[ConfigurationOverrideUpdate] = []
    mindsdb_config: Optional[MindsDBConfigurationUpdate] = None
    apply_immediately: bool = False
    change_reason: Optional[str] = None


# Environment variable discovery
class EnvironmentVariable(BaseModel):
    name: str
    value: Optional[str] = None
    is_set: bool = False
    is_managed: bool = False  # Whether it's managed by our config system
    category: Optional[ConfigCategoryEnum] = None
    description: Optional[str] = None


class EnvironmentVariablesResponse(BaseModel):
    variables: List[EnvironmentVariable]
    managed_count: int
    unmanaged_count: int
    categories: Dict[str, int]  # Count by category