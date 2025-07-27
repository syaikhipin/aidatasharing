"""
Environment Detection Utilities for AI Share Platform
Provides utilities to detect development environments and localhost connections for SSL configuration
"""

import os
import socket
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class EnvironmentDetector:
    """Utility class for detecting development environments and localhost connections"""
    
    # Localhost identifiers
    LOCALHOST_HOSTS = {
        'localhost',
        '127.0.0.1',
        '::1',
        '0.0.0.0'
    }
    
    # Development environment indicators
    DEVELOPMENT_INDICATORS = {
        'NODE_ENV': ['development', 'dev'],
        'ENVIRONMENT': ['development', 'dev', 'local'],
        'ENV': ['development', 'dev', 'local'],
        'FLASK_ENV': ['development'],
        'FASTAPI_ENV': ['development'],
        'DEBUG': ['true', '1', 'yes']
    }
    
    # Development port ranges (commonly used for local development)
    DEVELOPMENT_PORT_RANGES = [
        (3000, 3010),    # React/Next.js default range
        (8000, 8010),    # FastAPI/Django default range
        (5000, 5010),    # Flask default range
        (10100, 10200),  # Our custom proxy range
        (47334, 47334),  # MindsDB default
    ]
    
    @classmethod
    def is_development_environment(cls) -> bool:
        """
        Detect if running in development environment
        
        Returns:
            bool: True if development environment detected
        """
        try:
            # Check environment variables
            for env_var, dev_values in cls.DEVELOPMENT_INDICATORS.items():
                env_value = os.getenv(env_var, '').lower()
                if env_value in dev_values:
                    logger.info(f"🔍 Development environment detected via {env_var}={env_value}")
                    return True
            
            # Check if running on development ports
            if cls._is_running_on_development_ports():
                logger.info("🔍 Development environment detected via port analysis")
                return True
            
            # Check for development file indicators
            if cls._has_development_files():
                logger.info("🔍 Development environment detected via development files")
                return True
            
            logger.info("🔍 Production environment detected")
            return False
            
        except Exception as e:
            logger.warning(f"Failed to detect environment, defaulting to production: {e}")
            return False
    
    @classmethod
    def is_localhost_connection(cls, host: str, port: Optional[int] = None) -> bool:
        """
        Check if connection is to localhost
        
        Args:
            host: Hostname or IP address
            port: Optional port number
            
        Returns:
            bool: True if localhost connection
        """
        try:
            if not host:
                return False
            
            # Direct localhost check
            if host.lower() in cls.LOCALHOST_HOSTS:
                return True
            
            # Check if host resolves to localhost
            try:
                resolved_ip = socket.gethostbyname(host)
                if resolved_ip in cls.LOCALHOST_HOSTS:
                    return True
            except socket.gaierror:
                pass
            
            # Check development port ranges if port provided
            if port and cls._is_development_port(port):
                logger.debug(f"Host {host}:{port} considered localhost due to development port")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Failed to check localhost connection for {host}: {e}")
            return False
    
    @classmethod
    def should_disable_ssl(cls, host: str, port: Optional[int] = None, force_ssl: Optional[bool] = None) -> bool:
        """
        Determine if SSL should be disabled for a connection
        
        Args:
            host: Hostname or IP address
            port: Optional port number
            force_ssl: Explicit SSL setting (overrides auto-detection)
            
        Returns:
            bool: True if SSL should be disabled
        """
        try:
            # Explicit SSL setting takes precedence
            if force_ssl is not None:
                return not force_ssl
            
            # Only disable SSL for localhost in development
            is_localhost = cls.is_localhost_connection(host, port)
            is_development = cls.is_development_environment()
            
            should_disable = is_localhost and is_development
            
            if should_disable:
                logger.info(f"🔓 SSL disabled for localhost connection: {host}:{port} (development mode)")
            else:
                logger.info(f"🔒 SSL enabled for connection: {host}:{port}")
            
            return should_disable
            
        except Exception as e:
            logger.warning(f"Failed to determine SSL setting, defaulting to enabled: {e}")
            return False
    
    @classmethod
    def get_ssl_config_for_connection(cls, connector_type: str, host: str, port: Optional[int] = None, 
                                     existing_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get SSL configuration for a specific connector type and connection
        
        Args:
            connector_type: Type of connector (mysql, postgresql, etc.)
            host: Hostname or IP address
            port: Optional port number
            existing_config: Existing configuration to merge with
            
        Returns:
            Dict containing SSL configuration
        """
        try:
            config = existing_config.copy() if existing_config else {}
            
            should_disable = cls.should_disable_ssl(host, port, config.get('force_ssl'))
            
            # Apply connector-specific SSL configuration
            if connector_type == 'mysql':
                config['ssl_disabled'] = should_disable
                if should_disable:
                    # Remove any SSL-related parameters that might conflict
                    ssl_params = ['ssl_ca', 'ssl_cert', 'ssl_key', 'ssl_verify_cert', 'ssl_verify_identity']
                    for param in ssl_params:
                        config.pop(param, None)
                        
            elif connector_type == 'postgresql':
                if should_disable:
                    config['sslmode'] = 'disable'
                else:
                    # Use prefer as default for production (allows SSL if available)
                    config['sslmode'] = config.get('sslmode', 'prefer')
                    
            elif connector_type == 'mongodb':
                config['ssl'] = not should_disable
                
            elif connector_type in ['redshift', 'snowflake']:
                # These typically require SSL in production
                if should_disable:
                    config['sslmode'] = 'disable'
                else:
                    config['sslmode'] = config.get('sslmode', 'require')
                    
            elif connector_type == 'api':
                # For API connections, prefer HTTP for localhost in development
                if should_disable and host in cls.LOCALHOST_HOSTS:
                    # Convert HTTPS to HTTP for localhost in development
                    base_url = config.get('base_url', '')
                    if base_url.startswith('https://') and cls.is_localhost_connection(host, port):
                        # Replace https with http for localhost
                        config['base_url'] = base_url.replace('https://', 'http://', 1)
                        logger.info(f"🔓 API connection converted to HTTP for localhost: {config['base_url']}")
                    
                    # Set default protocol preference
                    config['prefer_http'] = True
                    config['ssl_verify'] = False
                else:
                    # Production or external APIs should use HTTPS
                    config['prefer_http'] = False
                    config['ssl_verify'] = True
                    
            elif connector_type == 'clickhouse':
                # ClickHouse SSL configuration
                if should_disable:
                    config['secure'] = False
                    config['verify'] = False
                else:
                    config['secure'] = config.get('secure', True)
                    config['verify'] = config.get('verify', True)
                    
            elif connector_type == 's3':
                # S3 SSL configuration
                if should_disable and host in cls.LOCALHOST_HOSTS:
                    # For localhost S3-compatible services (like MinIO)
                    config['use_ssl'] = False
                    config['verify'] = False
                else:
                    config['use_ssl'] = config.get('use_ssl', True)
                    config['verify'] = config.get('verify', True)
                    
            logger.debug(f"SSL config for {connector_type} connection to {host}:{port}: {config}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to generate SSL config: {e}")
            return existing_config or {}
    
    @classmethod
    def _is_running_on_development_ports(cls) -> bool:
        """Check if any development ports are in use (indicating dev environment)"""
        try:
            for start_port, end_port in cls.DEVELOPMENT_PORT_RANGES:
                for port in range(start_port, end_port + 1):
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(0.1)
                        result = sock.connect_ex(('127.0.0.1', port))
                        sock.close()
                        if result == 0:  # Port is open
                            return True
                    except:
                        continue
            return False
        except:
            return False
    
    @classmethod
    def _is_development_port(cls, port: int) -> bool:
        """Check if port is in development range"""
        for start_port, end_port in cls.DEVELOPMENT_PORT_RANGES:
            if start_port <= port <= end_port:
                return True
        return False
    
    @classmethod
    def _has_development_files(cls) -> bool:
        """Check for development-specific files"""
        dev_files = [
            '.env.development',
            '.env.local',
            'docker-compose.dev.yml',
            'package.json',  # Indicates Node.js development
            'requirements-dev.txt',
            'pyproject.toml'
        ]
        
        try:
            for file_name in dev_files:
                if os.path.exists(file_name) or os.path.exists(f"../{file_name}"):
                    return True
            return False
        except:
            return False


# Convenience functions for common use cases
def is_development() -> bool:
    """Check if running in development environment"""
    return EnvironmentDetector.is_development_environment()


def is_localhost(host: str, port: Optional[int] = None) -> bool:
    """Check if connection is to localhost"""
    return EnvironmentDetector.is_localhost_connection(host, port)


def should_disable_ssl(host: str, port: Optional[int] = None, force_ssl: Optional[bool] = None) -> bool:
    """Check if SSL should be disabled for connection"""
    return EnvironmentDetector.should_disable_ssl(host, port, force_ssl)


def get_ssl_config(connector_type: str, host: str, port: Optional[int] = None, 
                   existing_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get SSL configuration for connection"""
    return EnvironmentDetector.get_ssl_config_for_connection(
        connector_type, host, port, existing_config
    )