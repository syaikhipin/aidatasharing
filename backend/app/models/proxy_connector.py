"""
Secure Proxy Models for hiding real URLs and credentials
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import secrets


class ProxyConnector(Base):
    """
    Secure proxy connector that hides real connection details from users
    """
    __tablename__ = "proxy_connectors"

    id = Column(Integer, primary_key=True, index=True)
    proxy_id = Column(String(255), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    connector_type = Column(String(50), nullable=False)  # 'api', 'database', 'shared_link'
    
    # Proxy configuration
    proxy_url = Column(String(500), nullable=False)  # Public proxy URL
    access_token = Column(String(255), unique=True, default=lambda: secrets.token_urlsafe(32))
    
    # Hidden connection details (encrypted)
    real_connection_config = Column(JSON)  # Actual connection details
    real_credentials = Column(JSON)  # Actual credentials
    
    # Access control
    is_public = Column(Boolean, default=False)
    allowed_operations = Column(JSON)  # List of allowed operations
    rate_limit = Column(Integer, default=100)  # Requests per hour
    
    # Metadata
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    total_requests = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True))
    
    # Enhanced editing capabilities
    is_editable = Column(Boolean, default=True)
    supports_real_time = Column(Boolean, default=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="proxy_connectors")
    creator = relationship("User")
    access_logs = relationship("ProxyAccessLog", back_populates="proxy_connector")
    shared_links = relationship("SharedProxyLink", back_populates="proxy_connector")


class SharedProxyLink(Base):
    """
    Shared links that provide secure access to proxy connectors
    """
    __tablename__ = "shared_proxy_links"

    id = Column(Integer, primary_key=True, index=True)
    share_id = Column(String(255), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    proxy_connector_id = Column(Integer, ForeignKey("proxy_connectors.id"), nullable=False)
    
    # Link configuration
    name = Column(String(255), nullable=False)
    description = Column(Text)
    public_url = Column(String(500), nullable=False)  # User-facing URL
    
    # Access control
    is_public = Column(Boolean, default=False)
    requires_authentication = Column(Boolean, default=True)
    allowed_users = Column(JSON)  # List of user IDs or emails
    allowed_domains = Column(JSON)  # List of allowed email domains
    
    # Expiration and limits
    expires_at = Column(DateTime(timezone=True))
    max_uses = Column(Integer)
    current_uses = Column(Integer, default=0)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    proxy_connector = relationship("ProxyConnector", back_populates="shared_links")
    creator = relationship("User")
    access_logs = relationship("ProxyAccessLog", back_populates="shared_link")


class ProxyAccessLog(Base):
    """
    Access logs for proxy connector usage tracking
    """
    __tablename__ = "proxy_access_logs"

    id = Column(Integer, primary_key=True, index=True)
    proxy_connector_id = Column(Integer, ForeignKey("proxy_connectors.id"), nullable=False)
    shared_link_id = Column(Integer, ForeignKey("shared_proxy_links.id"), nullable=True)
    
    # Request details
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_ip = Column(String(45))  # IPv6 support
    user_agent = Column(Text)
    
    # Operation details
    operation_type = Column(String(100))  # 'query', 'api_call', 'file_access', etc.
    operation_details = Column(JSON)
    
    # Response details
    status_code = Column(Integer)
    response_size = Column(Integer)
    execution_time_ms = Column(Integer)
    
    # Metadata
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    proxy_connector = relationship("ProxyConnector", back_populates="access_logs")
    shared_link = relationship("SharedProxyLink", back_populates="access_logs")
    user = relationship("User")


class ProxyCredentialVault(Base):
    """
    Secure vault for storing encrypted credentials
    """
    __tablename__ = "proxy_credential_vault"

    id = Column(Integer, primary_key=True, index=True)
    vault_id = Column(String(255), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    credential_type = Column(String(50), nullable=False)  # 'api_key', 'database', 'oauth', etc.
    
    # Encrypted credential data
    encrypted_credentials = Column(Text, nullable=False)
    encryption_key_id = Column(String(255), nullable=False)
    
    # Metadata
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)
    
    # Relationships
    organization = relationship("Organization")
    creator = relationship("User")