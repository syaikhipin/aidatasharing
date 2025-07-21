from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.dataset import DatasetType, DatasetStatus
from app.models.organization import DataSharingLevel


class DatasetBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: DatasetType
    sharing_level: DataSharingLevel = DataSharingLevel.PRIVATE
    source_url: Optional[str] = None
    connection_params: Optional[Dict[str, Any]] = None
    connector_id: Optional[int] = None
    schema_info: Optional[Dict[str, Any]] = None
    allow_download: bool = True
    allow_api_access: bool = True


class DatasetCreate(DatasetBase):
    department_id: Optional[int] = None
    
    @validator('sharing_level')
    def validate_sharing_level(cls, v):
        # Validate sharing level
        if v not in [DataSharingLevel.PRIVATE, DataSharingLevel.ORGANIZATION, DataSharingLevel.PUBLIC]:
            raise ValueError('Invalid sharing level')
        return v


class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sharing_level: Optional[DataSharingLevel] = None
    department_id: Optional[int] = None
    connector_id: Optional[int] = None
    allow_download: Optional[bool] = None
    allow_api_access: Optional[bool] = None
    schema_info: Optional[Dict[str, Any]] = None


class DatasetOwner(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class DatasetResponse(DatasetBase):
    id: int
    status: DatasetStatus
    owner_id: int
    organization_id: int
    department_id: Optional[int] = None
    connector_id: Optional[int] = None
    size_bytes: Optional[int] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    mindsdb_table_name: Optional[str] = None
    mindsdb_database: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_accessed: Optional[datetime] = None
    
    owner: Optional[DatasetOwner] = None
    
    class Config:
        from_attributes = True


class DatasetUpload(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sharing_level: DataSharingLevel = DataSharingLevel.PRIVATE
    department_id: Optional[int] = None


class DatasetStats(BaseModel):
    dataset_id: int
    total_size: Optional[int] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    sharing_level: DataSharingLevel
    created_at: datetime
    last_accessed: Optional[datetime] = None
    recent_access: List[Dict[str, Any]] = []


class DatasetAccessLog(BaseModel):
    id: int
    dataset_id: int
    user_id: int
    access_type: str
    ip_address: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True