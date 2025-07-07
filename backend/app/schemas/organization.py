from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from app.models.organization import OrganizationType, DataSharingLevel, UserRole as UserRoleEnum


class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    pass  # organization_id is set automatically from URL parameter


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class Department(DepartmentBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: OrganizationType = OrganizationType.SMALL_BUSINESS
    allow_external_sharing: bool = False  # Always False - no cross-organization sharing
    default_sharing_level: DataSharingLevel = DataSharingLevel.ORGANIZATION  # Default within org
    website: Optional[str] = None
    contact_email: Optional[str] = None

    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Organization name must be at least 2 characters')
        return v.strip()
    
    @validator('allow_external_sharing')
    def validate_external_sharing(cls, v):
        if v is True:
            raise ValueError('External sharing is not supported - all data is organization-scoped')
        return False


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[OrganizationType] = None
    allow_external_sharing: Optional[bool] = None
    default_sharing_level: Optional[DataSharingLevel] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: Optional[bool] = None


class Organization(OrganizationBase):
    id: int
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationWithDepartments(Organization):
    departments: List[Department] = []


# User-Organization relationship schemas
class UserRoleAssignment(BaseModel):
    user_id: int
    organization_id: int
    department_id: Optional[int] = None
    role: UserRoleEnum


class OrganizationMember(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OrganizationInvite(BaseModel):
    email: str
    role: UserRoleEnum = UserRoleEnum.MEMBER
    department_id: Optional[int] = None


# Organization selection for registration
class OrganizationOption(BaseModel):
    id: int
    name: str
    type: OrganizationType
    description: Optional[str] = None 