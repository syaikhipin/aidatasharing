"""
SSL Middleware for flexible HTTPS handling
Supports automatic redirects and SSL detection based on environment
"""

import os
import logging
from typing import Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import RedirectResponse

logger = logging.getLogger(__name__)


class SSLMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle SSL/HTTPS redirects and enforce security policies
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.ssl_config = self._load_ssl_config()
        
    def _load_ssl_config(self) -> Dict[str, Any]:
        """Load SSL configuration from environment"""
        node_env = os.getenv("NODE_ENV", "development").lower()

        # Simple: production = SSL enabled, development = no SSL
        ssl_enabled = (node_env == "production")

        logger.info(f"SSL Middleware Config: node_env={node_env}, ssl_enabled={ssl_enabled}")

        return {
            "ssl_enabled": ssl_enabled
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request and handle SSL redirects if needed"""

        # Check if SSL redirect is needed
        if self._should_redirect_to_https(request):
            https_url = self._build_https_url(request)
            return RedirectResponse(url=https_url, status_code=301)

        # Add security headers for HTTPS responses
        response = await call_next(request)

        # Fix any HTTP redirects to use HTTPS in production
        if self._is_https_request(request) and response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get("location")
            if location and location.startswith("http://"):
                # Replace http:// with https:// to prevent protocol downgrade
                response.headers["location"] = location.replace("http://", "https://", 1)
                logger.info(f"Fixed redirect from HTTP to HTTPS: {location} -> {response.headers['location']}")

        if self._is_https_response(request):
            self._add_security_headers(response)

        return response
    
    def _should_redirect_to_https(self, request: Request) -> bool:
        """Determine if request should be redirected to HTTPS"""

        # Only redirect if SSL is enabled (NODE_ENV=production)
        if not self.ssl_config["ssl_enabled"]:
            return False

        # Skip if already HTTPS
        if self._is_https_request(request):
            return False

        host = request.headers.get("host", "")

        # Never redirect localhost/development hosts
        if self._is_development_host(host):
            return False

        return True
    
    def _is_https_request(self, request: Request) -> bool:
        """Check if request is already HTTPS"""
        
        # Check URL scheme
        if request.url.scheme == "https":
            return True
        
        # Check proxy headers
        forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
        if forwarded_proto == "https":
            return True
        
        # Check SSL header
        if request.headers.get("x-forwarded-ssl") == "on":
            return True
        
        return False
    
    def _is_development_host(self, host: str) -> bool:
        """Check if host is development/localhost"""
        dev_hosts = ["localhost", "127.0.0.1", "0.0.0.0"]
        return any(dev_host in host.lower() for dev_host in dev_hosts) or host.startswith("192.168.")
    
    def _build_https_url(self, request: Request) -> str:
        """Build HTTPS version of the current URL"""
        
        # Get host from headers (handles proxy situations)
        host = request.headers.get("host") or request.url.hostname
        
        # Remove default HTTPS port if present
        if ":443" in host:
            host = host.replace(":443", "")
        
        # Build HTTPS URL
        path_with_query = str(request.url.path)
        if request.url.query:
            path_with_query += f"?{request.url.query}"
        
        return f"https://{host}{path_with_query}"
    
    def _is_https_response(self, request: Request) -> bool:
        """Check if response should include HTTPS security headers"""
        return self._is_https_request(request)
    
    def _add_security_headers(self, response: Response):
        """Add security headers for HTTPS responses"""
        
        # Only add security headers if not already present
        headers_to_add = {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
        
        for header_name, header_value in headers_to_add.items():
            if header_name not in response.headers:
                response.headers[header_name] = header_value


class FlexibleSSLConfig:
    """
    Utility class for SSL configuration management
    """

    @staticmethod
    def get_ssl_settings() -> Dict[str, str]:
        """Get current SSL settings for debugging"""
        node_env = os.getenv("NODE_ENV", "development")
        ssl_enabled = node_env.lower() == "production"

        return {
            "NODE_ENV": node_env,
            "SSL_ENABLED": str(ssl_enabled)
        }

    @staticmethod
    def is_ssl_enabled() -> bool:
        """Check if SSL is currently enabled"""
        node_env = os.getenv("NODE_ENV", "development").lower()
        return node_env == "production"