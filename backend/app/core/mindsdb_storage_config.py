"""
MindsDB Storage Configuration Manager
Manages storage configuration that follows MindsDB's config patterns
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class MindsDBStorageConfig:
    """
    MindsDB-compatible storage configuration manager
    Reads storage configuration from MindsDB config file or environment variables
    """
    
    def __init__(self, mindsdb_config_path: Optional[str] = None):
        self.mindsdb_config_path = mindsdb_config_path or os.getenv(
            'MINDSDB_CONFIG_PATH', 
            '/Users/syaikhipin/Documents/program/simpleaisharing/mindsdb_config.json'
        )
        self._config_cache = None
        self._storage_config_cache = None
    
    def _load_mindsdb_config(self) -> Dict[str, Any]:
        """Load MindsDB configuration from JSON file"""
        if self._config_cache is not None:
            return self._config_cache
            
        try:
            if os.path.exists(self.mindsdb_config_path):
                with open(self.mindsdb_config_path, 'r') as f:
                    self._config_cache = json.load(f)
                    logger.info(f"Loaded MindsDB config from {self.mindsdb_config_path}")
                    return self._config_cache
            else:
                logger.warning(f"MindsDB config file not found at {self.mindsdb_config_path}")
                self._config_cache = {}
                return self._config_cache
        except Exception as e:
            logger.error(f"Failed to load MindsDB config: {e}")
            self._config_cache = {}
            return self._config_cache
    
    def get_storage_config(self) -> Dict[str, Any]:
        """
        Get storage configuration following MindsDB patterns
        Returns storage configuration compatible with MindsDB's permanent_storage and paths
        """
        if self._storage_config_cache is not None:
            return self._storage_config_cache
            
        config = self._load_mindsdb_config()
        storage_config = {
            'storage_type': 'local',  # default: local or s3
            'local': {},
            's3': {},
            'paths': {}
        }
        
        # 1. Check permanent_storage configuration (MindsDB pattern)
        permanent_storage = config.get('permanent_storage', {})
        storage_location = permanent_storage.get('location', 'absent')
        
        if storage_location == 's3':
            storage_config['storage_type'] = 's3'
            storage_config['s3'] = {
                'bucket_name': permanent_storage.get('bucket'),
                'access_key': os.getenv('AWS_ACCESS_KEY_ID') or os.getenv('S3_ACCESS_KEY_ID'),
                'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY') or os.getenv('S3_SECRET_ACCESS_KEY'),
                'region': os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
                'endpoint_url': os.getenv('S3_ENDPOINT_URL'),
                'use_ssl': os.getenv('S3_USE_SSL', 'true').lower() == 'true',
                'addressing_style': os.getenv('S3_ADDRESSING_STYLE', 'path')
            }
            logger.info(f"S3 config from permanent_storage: bucket={storage_config['s3']['bucket_name']}, endpoint={storage_config['s3']['endpoint_url']}")
        elif storage_location in ['local', 'absent']:
            storage_config['storage_type'] = 'local'
        
        # 2. Configure paths following MindsDB's paths structure
        paths_config = config.get('paths', {})
        
        # Get base storage directory
        storage_dir = None
        
        # Priority order: MindsDB paths.root -> MindsDB storage_dir -> Environment -> Default
        if 'root' in paths_config:
            storage_dir = paths_config['root']
            logger.info(f"Using storage directory from MindsDB paths.root: {storage_dir}")
        elif 'storage_dir' in config:
            storage_dir = config['storage_dir']
            logger.info(f"Using storage directory from MindsDB storage_dir: {storage_dir}")
        elif os.getenv('MINDSDB_STORAGE_DIR'):
            storage_dir = os.getenv('MINDSDB_STORAGE_DIR')
            logger.info(f"Using storage directory from MINDSDB_STORAGE_DIR: {storage_dir}")
        else:
            # Default storage directory
            storage_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                "storage"
            )
            logger.info(f"Using default storage directory: {storage_dir}")
        
        # Configure local storage paths following MindsDB structure
        storage_config['local'] = {
            'base_path': storage_dir,
            'content_path': paths_config.get('content', os.path.join(storage_dir, 'content')),
            'storage_path': paths_config.get('storage', os.path.join(storage_dir, 'storage')),
            'static_path': paths_config.get('static', os.path.join(storage_dir, 'static')),
            'tmp_path': paths_config.get('tmp', os.path.join(storage_dir, 'tmp')),
            'cache_path': paths_config.get('cache', os.path.join(storage_dir, 'cache')),
            'locks_path': paths_config.get('locks', os.path.join(storage_dir, 'locks')),
            'uploads_path': os.path.join(storage_dir, 'uploads'),  # Our uploads directory
            'datasets_path': os.path.join(storage_dir, 'datasets')  # Our datasets directory
        }
        
        storage_config['paths'] = storage_config['local']
        
        # 3. Override with environment variables only if MindsDB config doesn't specify storage
        env_storage_type = os.getenv('STORAGE_TYPE', '').lower()
        
        # Only use environment override if MindsDB permanent_storage is 'absent' or not configured
        if storage_location in ['absent', None] and env_storage_type in ['s3', 's3_compatible']:
            logger.info("MindsDB permanent_storage is 'absent', using environment STORAGE_TYPE override")
            storage_config['storage_type'] = 's3'
            # Update S3 config with environment variables
            storage_config['s3'].update({
                'bucket_name': os.getenv('S3_BUCKET_NAME') or storage_config['s3'].get('bucket_name'),
                'access_key': os.getenv('S3_ACCESS_KEY_ID') or os.getenv('AWS_ACCESS_KEY_ID') or storage_config['s3'].get('access_key'),
                'secret_key': os.getenv('S3_SECRET_ACCESS_KEY') or os.getenv('AWS_SECRET_ACCESS_KEY') or storage_config['s3'].get('secret_key'),
                'endpoint_url': os.getenv('S3_ENDPOINT_URL') or storage_config['s3'].get('endpoint_url'),
                'region': os.getenv('S3_REGION') or os.getenv('AWS_DEFAULT_REGION') or storage_config['s3'].get('region'),
                'use_ssl': os.getenv('S3_USE_SSL', 'true').lower() == 'true',
                'addressing_style': os.getenv('S3_ADDRESSING_STYLE', 'path')
            })
        
        # Always supplement S3 config with environment variables for credentials/endpoints
        if storage_config['storage_type'] == 's3':
            storage_config['s3'].update({
                'bucket_name': storage_config['s3'].get('bucket_name') or os.getenv('S3_BUCKET_NAME'),
                'access_key': storage_config['s3'].get('access_key') or os.getenv('S3_ACCESS_KEY_ID') or os.getenv('AWS_ACCESS_KEY_ID'),
                'secret_key': storage_config['s3'].get('secret_key') or os.getenv('S3_SECRET_ACCESS_KEY') or os.getenv('AWS_SECRET_ACCESS_KEY'),
                'endpoint_url': storage_config['s3'].get('endpoint_url') or os.getenv('S3_ENDPOINT_URL'),
                'region': storage_config['s3'].get('region') or os.getenv('S3_REGION') or os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
                'use_ssl': os.getenv('S3_USE_SSL', 'true').lower() == 'true',
                'addressing_style': os.getenv('S3_ADDRESSING_STYLE', 'path')
            })
            logger.info(f"Final S3 config: bucket={storage_config['s3']['bucket_name']}, endpoint={storage_config['s3']['endpoint_url']}, has_credentials={bool(storage_config['s3']['access_key'] and storage_config['s3']['secret_key'])}")
        
        self._storage_config_cache = storage_config
        return storage_config
    
    def get_storage_type(self) -> str:
        """Get the configured storage type (local or s3)"""
        return self.get_storage_config()['storage_type']
    
    def get_local_storage_config(self) -> Dict[str, str]:
        """Get local storage configuration"""
        return self.get_storage_config()['local']
    
    def get_s3_storage_config(self) -> Dict[str, Any]:
        """Get S3 storage configuration"""
        return self.get_storage_config()['s3']
    
    def get_uploads_path(self) -> str:
        """Get the uploads directory path"""
        config = self.get_storage_config()
        if config['storage_type'] == 'local':
            return config['local']['uploads_path']
        else:
            return 'uploads'  # S3 prefix
    
    def get_datasets_path(self) -> str:
        """Get the datasets directory path"""
        config = self.get_storage_config()
        if config['storage_type'] == 'local':
            return config['local']['datasets_path']
        else:
            return 'datasets'  # S3 prefix
    
    def ensure_local_directories(self):
        """Ensure all local storage directories exist"""
        if self.get_storage_type() == 'local':
            local_config = self.get_local_storage_config()
            for path_name, path_value in local_config.items():
                if path_name.endswith('_path') and path_value:
                    try:
                        Path(path_value).mkdir(parents=True, exist_ok=True)
                        logger.debug(f"Ensured directory exists: {path_value}")
                    except Exception as e:
                        logger.error(f"Failed to create directory {path_value}: {e}")
    
    def is_s3_configured(self) -> bool:
        """Check if S3 storage is properly configured"""
        if self.get_storage_type() != 's3':
            return False
            
        s3_config = self.get_s3_storage_config()
        required_fields = ['bucket_name', 'access_key', 'secret_key']
        
        return all(s3_config.get(field) for field in required_fields)
    
    def get_mindsdb_compatible_paths(self) -> Dict[str, str]:
        """
        Get paths in MindsDB-compatible format for integration
        Returns paths that can be used by MindsDB for file operations
        """
        storage_config = self.get_storage_config()
        
        if storage_config['storage_type'] == 'local':
            base_path = storage_config['local']['base_path']
            return {
                'root': base_path,
                'content': storage_config['local']['content_path'],
                'storage': storage_config['local']['storage_path'], 
                'static': storage_config['local']['static_path'],
                'tmp': storage_config['local']['tmp_path'],
                'cache': storage_config['local']['cache_path'],
                'locks': storage_config['local']['locks_path'],
                'uploads': storage_config['local']['uploads_path'],
                'datasets': storage_config['local']['datasets_path']
            }
        else:
            # For S3, return logical paths
            return {
                'root': 's3_storage',
                'content': 'content',
                'storage': 'storage',
                'static': 'static', 
                'tmp': 'tmp',
                'cache': 'cache',
                'locks': 'locks',
                'uploads': 'uploads',
                'datasets': 'datasets'
            }
    
    def refresh_config(self):
        """Refresh configuration cache - useful for dynamic config changes"""
        self._config_cache = None
        self._storage_config_cache = None
        logger.info("Configuration cache refreshed")
    
    def update_mindsdb_config(self, updates: Dict[str, Any], create_backup: bool = True):
        """
        Update the MindsDB configuration file with new values
        
        Args:
            updates: Dictionary of configuration updates
            create_backup: Whether to create a backup of the original file
        """
        try:
            config = self._load_mindsdb_config()
            
            # Create backup if requested
            if create_backup and os.path.exists(self.mindsdb_config_path):
                backup_path = f"{self.mindsdb_config_path}.backup"
                import shutil
                shutil.copy2(self.mindsdb_config_path, backup_path)
                logger.info(f"Created backup at {backup_path}")
            
            # Update config
            def deep_update(target, source):
                for key, value in source.items():
                    if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                        deep_update(target[key], value)
                    else:
                        target[key] = value
            
            deep_update(config, updates)
            
            # Write updated config
            with open(self.mindsdb_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Refresh cache
            self.refresh_config()
            logger.info(f"Updated MindsDB configuration at {self.mindsdb_config_path}")
            
        except Exception as e:
            logger.error(f"Failed to update MindsDB config: {e}")
            raise

# Global instance
mindsdb_storage_config = MindsDBStorageConfig()