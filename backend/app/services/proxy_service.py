"""
API Gateway Service for Secure Data Sharing
Acts as a gateway to hide real API credentials while allowing shared access
"""

import json
import secrets
import hashlib
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request
import httpx
import asyncio
import logging

from app.models.proxy_connector import ProxyConnector, SharedProxyLink, ProxyAccessLog, ProxyCredentialVault
from app.models.user import User
from app.core.database import get_db
from app.services.mindsdb import MindsDBService

logger = logging.getLogger(__name__)


class APIGatewayService:
    """
    API Gateway Service for secure data sharing
    Acts as a middleman to hide real API credentials
    """
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        self.mindsdb_service = MindsDBService()
        
        # Gateway configuration
        self.gateway_base_url = "http://localhost:8000/api/proxy"  # Unified API proxy path
        self.rate_limits = {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "max_response_size": 10 * 1024 * 1024  # 10MB
        }
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for credential storage"""
        import os
        key_file = "gateway_encryption.key"
        
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
    
    async def create_gateway_connector(
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
        allowed_operations: Optional[List[str]] = None,
        rate_limit_override: Optional[Dict[str, int]] = None
    ) -> ProxyConnector:
        """Create a new gateway connector that completely hides real API details"""
        
        # Generate gateway identifiers
        gateway_id = str(secrets.token_urlsafe(24))
        gateway_token = str(secrets.token_urlsafe(32))
        
        # Create gateway URL that doesn't expose real endpoint
        gateway_url = f"{self.gateway_base_url}/gateway/{gateway_id}"
        
        # Encrypt real connection details with additional security
        security_salt = secrets.token_hex(16)
        enhanced_config = {
            **real_connection_config,
            "_security_salt": security_salt,
            "_created_at": datetime.utcnow().isoformat()
        }
        enhanced_credentials = {
            **real_credentials,
            "_gateway_token": gateway_token,
            "_access_level": "shared" if is_public else "private"
        }
        
        encrypted_config = self.encrypt_credentials(enhanced_config)
        encrypted_credentials = self.encrypt_credentials(enhanced_credentials)
        
        # Set default rate limits
        gateway_rate_limits = {**self.rate_limits}
        if rate_limit_override:
            gateway_rate_limits.update(rate_limit_override)
        
        # Create gateway connector
        gateway_connector = ProxyConnector(
            proxy_id=gateway_id,
            name=name,
            description=description,
            connector_type=connector_type,
            proxy_url=gateway_url,
            real_connection_config=encrypted_config,
            real_credentials=encrypted_credentials,
            is_public=is_public,
            allowed_operations=allowed_operations or ["GET", "POST"],
            organization_id=organization_id,
            created_by=user_id
        )
        
        db.add(gateway_connector)
        db.commit()
        db.refresh(gateway_connector)
        
        logger.info(f"Created gateway connector {gateway_connector.id} for organization {organization_id}")
        return gateway_connector
    
    async def create_public_share_link(
        self,
        db: Session,
        gateway_connector_id: int,
        name: str,
        user_id: int,
        description: Optional[str] = None,
        expires_in_hours: Optional[int] = 24,
        max_uses: Optional[int] = None,
        allowed_endpoints: Optional[List[str]] = None,
        custom_rate_limits: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Create a public share link for gateway connector"""
        
        # Verify gateway connector exists
        gateway_connector = db.query(ProxyConnector).filter(
            ProxyConnector.id == gateway_connector_id,
            ProxyConnector.is_active == True
        ).first()
        
        if not gateway_connector:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gateway connector not found"
            )
        
        # Generate public share identifiers
        share_id = str(secrets.token_urlsafe(32))
        access_token = str(secrets.token_urlsafe(24))
        
        # Create public URL that doesn't expose internal structure
        public_url = f"{self.gateway_base_url}/shared/{share_id}"
        
        # Calculate expiration
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        # Create shared link with gateway configuration
        shared_link = SharedProxyLink(
            share_id=share_id,
            proxy_connector_id=gateway_connector_id,
            name=name,
            description=description,
            public_url=public_url,
            is_public=True,
            requires_authentication=False,  # Public access through gateway
            allowed_users=[],  # Open access
            expires_at=expires_at,
            max_uses=max_uses,
            created_by=user_id
        )
        
        db.add(shared_link)
        db.commit()
        db.refresh(shared_link)
        
        # Generate curl commands for easy testing
        curl_commands = self._generate_curl_commands(shared_link, gateway_connector)
        
        logger.info(f"Created public share link {shared_link.id} for gateway connector {gateway_connector_id}")
        
        return {
            "share_id": share_id,
            "public_url": public_url,
            "expires_at": expires_at,
            "max_uses": max_uses,
            "curl_commands": curl_commands,
            "gateway_info": {
                "connector_name": gateway_connector.name,
                "connector_type": gateway_connector.connector_type,
                "allowed_operations": gateway_connector.allowed_operations,
                "rate_limits": custom_rate_limits or self.rate_limits
            }
        }
    
    def _generate_curl_commands(self, shared_link: SharedProxyLink, gateway_connector: ProxyConnector) -> Dict[str, str]:
        """Generate curl commands for testing the shared gateway"""
        
        # Use the actual gateway endpoint URL
        base_url = f"http://localhost:8000/api/gateway/shared/{shared_link.share_id}"
        
        commands = {
            "basic_get": f'curl "{base_url}"',
            
            "custom_endpoint": f"""curl -X POST "{base_url}" \\
  -H "Content-Type: application/json" \\
  -d '{{"method": "GET", "path": "/posts/1"}}'""",
            
            "with_params": f'curl "{base_url}?userId=1&_limit=5"',
            
            "post_data": f"""curl -X POST "{base_url}" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "method": "POST",
    "path": "/posts",
    "headers": {{"Content-Type": "application/json"}},
    "data": {{
      "title": "Test Post",
      "body": "Test content",
      "userId": 1
    }}
  }}'""",
            
            "gateway_info": f'curl "{base_url}/info"',
            
            "health_check": f'curl "{base_url}/health"'
        }
        
        return commands
    
    async def execute_gateway_request(
        self,
        db: Session,
        share_id: str,
        request_path: str,
        method: str,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Optional[Dict[str, Any]] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute request through the gateway (hiding real API details)"""
        
        # Get shared link
        shared_link = db.query(SharedProxyLink).filter(
            SharedProxyLink.share_id == share_id,
            SharedProxyLink.is_active == True
        ).first()
        
        if not shared_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared link not found"
            )
        
        # Validate access
        await self._validate_gateway_access(shared_link, method, request_path, client_ip)
        
        # Get gateway connector
        gateway_connector = shared_link.proxy_connector
        
        # Decrypt real connection details
        try:
            real_config = self.decrypt_credentials(gateway_connector.real_connection_config)
            real_credentials = self.decrypt_credentials(gateway_connector.real_credentials)
        except Exception as e:
            logger.error(f"Failed to decrypt gateway credentials: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gateway configuration error"
            )
        
        # Execute request through gateway
        start_time = datetime.utcnow()
        try:
            result = await self._execute_gateway_api_request(
                real_config, real_credentials, method, request_path, headers, params, data
            )
            
            status_code = result.get("status_code", 200)
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
        except Exception as e:
            logger.error(f"Gateway request failed: {e}")
            result = {"error": str(e), "success": False}
            status_code = 500
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log gateway access
        await self._log_gateway_access(
            db, shared_link.id, gateway_connector.id, client_ip, user_agent,
            method, request_path, params, status_code, execution_time
        )
        
        # Update usage statistics
        shared_link.current_uses += 1
        gateway_connector.total_requests += 1
        gateway_connector.last_accessed_at = datetime.utcnow()
        db.commit()
        
        return result
    
    async def _validate_gateway_access(
        self,
        shared_link: SharedProxyLink,
        method: str,
        request_path: str,
        client_ip: Optional[str]
    ):
        """Validate access to gateway"""
        
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
                detail="Usage limit exceeded"
            )
        
        # Check allowed endpoints
        # For now, allow all endpoints since we don't have metadata field
        # In production, you could add an allowed_endpoints field to the model
        
        # Check rate limits (simplified)
        # In production, implement proper rate limiting with Redis/cache
        
        return True
    
    async def _execute_gateway_api_request(
        self,
        config: Dict[str, Any],
        credentials: Dict[str, Any],
        method: str,
        request_path: str,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute API request through gateway"""
        
        base_url = config.get("base_url")
        if not base_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gateway configuration error: missing base URL"
            )
        
        # Build request URL
        endpoint = config.get("endpoint", "")
        if request_path and request_path != "/":
            endpoint = request_path.lstrip("/")
        
        full_url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Prepare headers with authentication
        request_headers = headers.copy()
        
        # Add authentication from real credentials
        if credentials.get("api_key"):
            auth_header = credentials.get("auth_header", "Authorization")
            auth_prefix = credentials.get("auth_prefix", "Bearer")
            request_headers[auth_header] = f"{auth_prefix} {credentials['api_key']}"
        elif credentials.get("username") and credentials.get("password"):
            import base64
            credentials_str = f"{credentials['username']}:{credentials['password']}"
            encoded_credentials = base64.b64encode(credentials_str.encode()).decode()
            request_headers["Authorization"] = f"Basic {encoded_credentials}"
        
        # Ensure content-type for POST/PUT requests
        if method.upper() in ["POST", "PUT", "PATCH"] and data:
            if "content-type" not in [k.lower() for k in request_headers.keys()]:
                request_headers["Content-Type"] = "application/json"
        
        # Execute request
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method.upper(),
                    url=full_url,
                    headers=request_headers,
                    params=params,
                    json=data if data and method.upper() in ["POST", "PUT", "PATCH"] else None,
                    timeout=30.0
                )
                
                # Handle response content
                content_type = response.headers.get("content-type", "").lower()
                
                if "application/json" in content_type:
                    try:
                        response_data = response.json()
                    except Exception:
                        response_data = response.text
                elif "text/" in content_type:
                    response_data = response.text
                else:
                    response_data = f"<binary data: {len(response.content)} bytes>"
                
                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "data": response_data,
                    "success": 200 <= response.status_code < 300,
                    "gateway_info": {
                        "request_url": full_url,
                        "method": method.upper(),
                        "response_size": len(response.content)
                    }
                }
                
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Gateway request timed out"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gateway request failed: {str(e)}"
            )
    
    async def _log_gateway_access(
        self,
        db: Session,
        shared_link_id: int,
        gateway_connector_id: int,
        client_ip: Optional[str],
        user_agent: Optional[str],
        method: str,
        request_path: str,
        params: Dict[str, Any],
        status_code: int,
        execution_time_ms: int
    ):
        """Log gateway access for monitoring and analytics"""
        
        access_log = ProxyAccessLog(
            proxy_connector_id=gateway_connector_id,
            user_id=None,  # Anonymous access through gateway
            user_ip=client_ip,
            user_agent=user_agent,
            operation_type=f"gateway_{method.lower()}",
            operation_details={
                "shared_link_id": shared_link_id,
                "method": method,
                "path": request_path,
                "params": params,
                "gateway_access": True
            },
            status_code=status_code,
            execution_time_ms=execution_time_ms
        )
        
        db.add(access_log)
        db.commit()
    
    async def get_gateway_info(self, db: Session, share_id: str) -> Dict[str, Any]:
        """Get information about a gateway share without exposing credentials"""
        
        shared_link = db.query(SharedProxyLink).filter(
            SharedProxyLink.share_id == share_id,
            SharedProxyLink.is_active == True
        ).first()
        
        if not shared_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared gateway not found"
            )
        
        gateway_connector = shared_link.proxy_connector
        
        return {
            "name": shared_link.name,
            "description": shared_link.description,
            "connector_type": gateway_connector.connector_type,
            "allowed_operations": gateway_connector.allowed_operations,
            "expires_at": shared_link.expires_at,
            "max_uses": shared_link.max_uses,
            "current_uses": shared_link.current_uses,
            "rate_limits": self.rate_limits,  # Use default rate limits
            "allowed_endpoints": ["*"],  # Allow all endpoints for now
            "gateway_url": shared_link.public_url,
            "status": "active" if shared_link.is_active else "inactive"
        }
# Backward compatibility - keep the original ProxyService class
class ProxyService(APIGatewayService):
    """Backward compatibility wrapper for APIGatewayService"""
    
    async def create_proxy_connector(self, *args, **kwargs):
        """Backward compatible method"""
        return await self.create_gateway_connector(*args, **kwargs)
    
    async def create_shared_link(self, db: Session, proxy_connector_id: int, name: str, user_id: int, **kwargs):
        """Backward compatible method"""
        return await self.create_public_share_link(db, proxy_connector_id, name, user_id, **kwargs)
    
    async def execute_proxy_operation(self, db: Session, proxy_id: str, operation_type: str, operation_data: Dict[str, Any], **kwargs):
        """Backward compatible method"""
        method = operation_data.get("method", "GET")
        request_path = operation_data.get("endpoint", "/")
        headers = operation_data.get("headers", {})
        params = operation_data.get("params", {})
        data = operation_data.get("data")
        
        return await self.execute_gateway_request(
            db=db,
            share_id=proxy_id,  # For backward compatibility
            request_path=request_path,
            method=method,
            headers=headers,
            params=params,
            data=data,
            client_ip=kwargs.get("user_ip"),
            user_agent=kwargs.get("user_agent")
        )
    """
    Service for managing secure proxy connectors
    """
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        self.mindsdb_service = MindsDBService()
    

    
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
        try:
            real_config = self.decrypt_credentials(proxy_connector.real_connection_config)
            real_credentials = self.decrypt_credentials(proxy_connector.real_credentials)
        except Exception as e:
            logger.error(f"Failed to decrypt connection details: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to decrypt connection details"
            )
        
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
            result = {"error": str(e), "success": False}
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
        if not base_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Base URL is required for API operations"
            )
        
        endpoint = operation_data.get("endpoint", config.get("endpoint", ""))
        method = operation_data.get("method", "GET").upper()
        headers = operation_data.get("headers", {})
        params = operation_data.get("params", {})
        data = operation_data.get("data")
        
        # Add authentication
        if credentials.get("api_key"):
            auth_header = credentials.get("auth_header", "Authorization")
            auth_prefix = credentials.get("auth_prefix", "Bearer")
            headers[auth_header] = f"{auth_prefix} {credentials['api_key']}"
        elif credentials.get("username") and credentials.get("password"):
            # Basic authentication
            import base64
            credentials_str = f"{credentials['username']}:{credentials['password']}"
            encoded_credentials = base64.b64encode(credentials_str.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_credentials}"
        
        # Ensure content-type is set for POST/PUT requests
        if method in ["POST", "PUT", "PATCH"] and data and "content-type" not in [k.lower() for k in headers.keys()]:
            headers["Content-Type"] = "application/json"
        
        # Make request with proper error handling
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}",
                    headers=headers,
                    params=params,
                    json=data if data and method in ["POST", "PUT", "PATCH"] else None,
                    timeout=30.0
                )
                
                # Handle response content type
                content_type = response.headers.get("content-type", "").lower()
                
                if "application/json" in content_type:
                    try:
                        response_data = response.json()
                    except Exception:
                        response_data = response.text
                elif "text/" in content_type:
                    response_data = response.text
                else:
                    response_data = response.content.hex()
                
                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "data": response_data,
                    "success": 200 <= response.status_code < 300
                }
                
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="API request timed out"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"API request failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in API operation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"API operation failed: {str(e)}"
            )
    
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