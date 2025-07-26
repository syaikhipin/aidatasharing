from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class DataSharingLevel(str, enum.Enum):
    """Data sharing levels - simplified 3-level structure"""
    PRIVATE = "private"  # Accessible to owner only
    ORGANIZATION = "organization"  # Accessible to all members within the organization (internal level)
    PUBLIC = "public"  # Accessible to everyone


class OrganizationType(str, enum.Enum):
    """Organization types"""
    ENTERPRISE = "enterprise"
    SMALL_BUSINESS = "small_business"
    NONPROFIT = "nonprofit"
    EDUCATIONAL = "educational"
    GOVERNMENT = "government"
    PERSONAL = "personal"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)  # URL-friendly name
    description = Column(Text, nullable=True)
    type = Column(Enum(OrganizationType), default=OrganizationType.SMALL_BUSINESS)
    
    # Settings
    is_active = Column(Boolean, default=True)
    allow_external_sharing = Column(Boolean, default=False)  # Allow sharing outside org
    default_sharing_level = Column(Enum(DataSharingLevel), default=DataSharingLevel.ORGANIZATION)
    
    # Contact info
    website = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships - using string references to avoid circular imports
    users = relationship("User", back_populates="organization", lazy="dynamic")


class UserRole(str, enum.Enum):
    """User roles within organization"""
    OWNER = "owner"  # Organization owner (full access)
    ADMIN = "admin"  # Organization admin (manage users, settings)
    MANAGER = "manager"  # Manager (manage organization data)
    MEMBER = "member"  # Regular member (view/create data)
    VIEWER = "viewer"  # Read-only access