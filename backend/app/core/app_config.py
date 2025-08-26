"""
Centralized Application Configuration for AI Share Platform
"""

import os
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class SecurityConfig:
    """Security configuration settings"""
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    JWT_ALGORITHM: str = "HS256"


@dataclass
class ServicesConfig:
    """Services configuration settings"""
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins from environment or defaults"""
        cors_origins = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
        return [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
    
    def get_mindsdb_url(self) -> str:
        """Get MindsDB URL from environment or default"""
        return os.getenv("MINDSDB_URL", "http://localhost:47334")


@dataclass 
class IntegrationsConfig:
    """External integrations configuration"""
    
    @property
    def GOOGLE_API_KEY(self) -> Optional[str]:
        """Get Google API key from environment"""
        return os.getenv("GOOGLE_API_KEY")
    
    @property
    def CONNECTOR_CONNECTION_TIMEOUT(self) -> int:
        """Get connector connection timeout from environment"""
        return int(os.getenv("CONNECTOR_TIMEOUT", "30"))


@dataclass
class ProxyConfig:
    """Proxy service configuration"""
    
    def get_proxy_ports(self) -> dict:
        """Get proxy port configuration"""
        return {
            "mysql": int(os.getenv("PROXY_MYSQL_PORT", "10101")),
            "postgresql": int(os.getenv("PROXY_POSTGRESQL_PORT", "10102")),
            "api": int(os.getenv("PROXY_API_PORT", "10103")),
            "clickhouse": int(os.getenv("PROXY_CLICKHOUSE_PORT", "10104")),
            "mongodb": int(os.getenv("PROXY_MONGODB_PORT", "10105")),
            "s3": int(os.getenv("PROXY_S3_PORT", "10106")),
            "shared": int(os.getenv("PROXY_SHARED_PORT", "10107"))
        }
    
    @property
    def PROXY_ENABLED(self) -> bool:
        """Check if proxy service is enabled"""
        return os.getenv("ENABLE_PROXY_SERVICE", "true").lower() == "true"
    
    @property
    def PROXY_HOST(self) -> str:
        """Get proxy host"""
        return os.getenv("PROXY_HOST", "localhost")


@dataclass
class AppConfig:
    """Main application configuration"""
    security: SecurityConfig
    services: ServicesConfig
    integrations: IntegrationsConfig
    proxy: ProxyConfig


def get_app_config() -> AppConfig:
    """Get centralized application configuration"""
    return AppConfig(
        security=SecurityConfig(),
        services=ServicesConfig(),
        integrations=IntegrationsConfig(),
        proxy=ProxyConfig()
    )