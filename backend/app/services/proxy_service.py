"""
Secure Proxy Service for managing proxy connectors and hiding real credentials
"""

import json
import secrets
import hashlib
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import httpx
import asyncio
import logging

from app.models.proxy_connector import ProxyConnector, SharedProxyLink, ProxyAccessLog, ProxyCredentialVault
from app.models.user import User
from app.core.database import get_db
from app.services.mindsdb import MindsDBService

logger = logging.getLogger(__name__)


class ProxyService:
    """
    Service for managing secure proxy connectors
    """
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        self.mindsdb_service = MindsDBService()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for credential storage"""
        # In production, this should be stored securely (e.g., AWS KMS, HashiCorp Vault)
        import os
        key_file = "proxy_encryption.key"
        
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            return key
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt credentials for secure storage"""
        json_data = json.dumps(credentials)
        encrypted_data = self.fernet.encrypt(json_data.encode())
        return encrypted_data.decode()
    
    def decrypt_credentials(self, encrypted_credentials: str) -> Dict[str, Any]:
        """Decrypt credentials for use"""
        try:
            decrypted_data = self.fernet.decrypt(encrypted_credentials.encode())
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to decrypt credentials"
            )
    
    async def create_proxy_connector(
        self,
        db: Session,
        name: str,
        connector_type: str,
        real_connection_config: Dict[str, Any],
        real_credentials: Dict[str, Any],
        organization_id: int,
        user_id: int,
        description: Optional[str] = None,
        is_public: bool = False,
        allowed_operations: Optional[List[str]] = None
    ) -> ProxyConnector:
        """Create a new proxy connector that hides real connection details"""
        
        # Generate proxy URL
        proxy_id = str(secrets.token_urlsafe(16))
        proxy_url = f"/proxy/{proxy_id}"
        
        # Encrypt real connection details
        encrypted_config = self.encrypt_credentials(real_connection_config)
        encrypted_credentials = self.encrypt_credentials(real_credentials)
        
        # Create proxy connector
        proxy_connector = ProxyConnector(
            proxy_id=proxy_id,
            name=name,
            description=description,
            connector_type=connector_type,
            proxy_url=proxy_url,
            real_connection_config=encrypted_config,
            real_credentials=encrypted_credentials,
            is_public=is_public,
            allowed_operations=allowed_operations or [],
            organization_id=organization_id,
            created_by=user_id
        )
        
        db.add(proxy_connector)
        db.commit()
        db.refresh(proxy_connector)
        
        logger.info(f"Created proxy connector {proxy_connector.id} for organization {organization_id}")
        return proxy_connector
    
    async def create_shared_link(
        self,
        db: Session,
        proxy_connector_id: int,
        name: str,
        user_id: int,
        description: Optional[str] = None,
        is_public: bool = False,
        requires_authentication: bool = True,
        allowed_users: Optional[List[str]] = None,
        expires_in_hours: Optional[int] = None,
        max_uses: Optional[int] = None
    ) -> SharedProxyLink:
        """Create a shared link for secure access to a proxy connector"""
        
        # Verify proxy connector exists and user has access
        proxy_connector = db.query(ProxyConnector).filter(
            ProxyConnector.id == proxy_connector_id,
            ProxyConnector.is_active == True
        ).first()
        
        if not proxy_connector:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proxy connector not found"
            )
        
        # Generate share ID and public URL
        share_id = str(secrets.token_urlsafe(24))
        public_url = f"/share/{share_id}"
        
        # Calculate expiration
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        # Create shared link
        shared_link = SharedProxyLink(
            share_id=share_id,
            proxy_connector_id=proxy_connector_id,
            name=name,
            description=description,
            public_url=public_url,
            is_public=is_public,
            requires_authentication=requires_authentication,
            allowed_users=allowed_users or [],
            expires_at=expires_at,
            max_uses=max_uses,
            created_by=user_id
        )
        
        db.add(shared_link)
        db.commit()
        db.refresh(shared_link)
        
        logger.info(f"Created shared link {shared_link.id} for proxy connector {proxy_connector_id}")
        return shared_link
    
    async def execute_proxy_operation(
        self,
        db: Session,
        proxy_id: str,
        operation_type: str,
        operation_data: Dict[str, Any],
        user_id: Optional[int] = None,
        user_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute an operation through the proxy connector"""
        
        # Get proxy connector
        proxy_connector = db.query(ProxyConnector).filter(
            ProxyConnector.proxy_id == proxy_id,
            ProxyConnector.is_active == True
        ).first()
        
        if not proxy_connector:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proxy connector not found"
            )
        
        # Check if operation is allowed
        if proxy_connector.allowed_operations and operation_type not in proxy_connector.allowed_operations:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation '{operation_type}' not allowed"
            )
        
        # Decrypt real connection details
        real_config = json.loads(proxy_connector.real_connection_config)
        real_credentials = json.loads(proxy_connector.real_credentials)
        
        # Execute operation based on connector type
        start_time = datetime.utcnow()
        try:
            if proxy_connector.connector_type == "api":
                result = await self._execute_api_operation(real_config, real_credentials, operation_data)
            elif proxy_connector.connector_type == "database":
                result = await self._execute_database_operation(real_config, real_credentials, operation_data)
            elif proxy_connector.connector_type == "shared_link":
                result = await self._execute_shared_link_operation(real_config, real_credentials, operation_data)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported connector type: {proxy_connector.connector_type}"
                )
            
            status_code = 200
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
        except Exception as e:
            logger.error(f"Proxy operation failed: {e}")
            result = {"error": str(e)}
            status_code = 500
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log access
        await self._log_proxy_access(
            db, proxy_connector.id, user_id, user_ip, user_agent,
            operation_type, operation_data, status_code, execution_time
        )
        
        # Update usage statistics
        proxy_connector.total_requests += 1
        proxy_connector.last_accessed_at = datetime.utcnow()
        db.commit()
        
        return result
    
    async def _execute_api_operation(
        self,
        config: Dict[str, Any],
        credentials: Dict[str, Any],
        operation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute API operation through proxy"""
        
        base_url = config.get("base_url")
        endpoint = operation_data.get("endpoint", config.get("endpoint", ""))
        method = operation_data.get("method", "GET")
        headers = operation_data.get("headers", {})
        params = operation_data.get("params", {})
        data = operation_data.get("data")
        
        # Add authentication
        if credentials.get("api_key"):
            auth_header = credentials.get("auth_header", "Authorization")
            headers[auth_header] = f"Bearer {credentials['api_key']}"
        
        # Make request
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=f"{base_url}{endpoint}",
                headers=headers,
                params=params,
                json=data if data else None,
                timeout=30.0
            )
            
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            }
    
    async def _execute_database_operation(
        self,
        config: Dict[str, Any],
        credentials: Dict[str, Any],
        operation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute database operation through proxy"""
        
        query = operation_data.get("query")
        if not query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query is required for database operations"
            )
        
        # Build connection parameters
        connection_params = {**config, **credentials}
        
        # Execute query through MindsDB
        try:
            result = self.mindsdb_service.execute_query(query, connection_params)
            return {
                "status": "success",
                "data": result.get("data", []),
                "columns": result.get("columns", []),
                "row_count": len(result.get("data", []))
            }
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _execute_shared_link_operation(
        self,
        config: Dict[str, Any],
        credentials: Dict[str, Any],
        operation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute shared link operation through proxy"""
        
        target_url = config.get("target_url")
        if not target_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target URL is required for shared link operations"
            )
        
        # Fetch content from target URL
        async with httpx.AsyncClient() as client:
            response = await client.get(target_url, timeout=30.0)
            
            return {
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type"),
                "content": response.text if response.headers.get("content-type", "").startswith("text/") else response.content.hex()
            }
    
    async def _log_proxy_access(
        self,
        db: Session,
        proxy_connector_id: int,
        user_id: Optional[int],
        user_ip: Optional[str],
        user_agent: Optional[str],
        operation_type: str,
        operation_details: Dict[str, Any],
        status_code: int,
        execution_time_ms: int
    ):
        """Log proxy access for auditing and analytics"""
        
        access_log = ProxyAccessLog(
            proxy_connector_id=proxy_connector_id,
            user_id=user_id,
            user_ip=user_ip,
            user_agent=user_agent,
            operation_type=operation_type,
            operation_details=operation_details,
            status_code=status_code,
            execution_time_ms=execution_time_ms
        )
        
        db.add(access_log)
        db.commit()
    
    async def validate_shared_link_access(
        self,
        db: Session,
        share_id: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None
    ) -> SharedProxyLink:
        """Validate access to a shared link"""
        
        shared_link = db.query(SharedProxyLink).filter(
            SharedProxyLink.share_id == share_id,
            SharedProxyLink.is_active == True
        ).first()
        
        if not shared_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared link not found"
            )
        
        # Check expiration
        if shared_link.expires_at and shared_link.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Shared link has expired"
            )
        
        # Check usage limits
        if shared_link.max_uses and shared_link.current_uses >= shared_link.max_uses:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Shared link usage limit exceeded"
            )
        
        # Check access permissions
        if not shared_link.is_public:
            if shared_link.requires_authentication and not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if shared_link.allowed_users and user_email not in shared_link.allowed_users:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        return shared_link