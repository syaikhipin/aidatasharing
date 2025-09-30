"""
Environment Configuration Management API
Manages .env file directly without database dependencies
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from app.core.auth import get_current_superuser
from app.models.user import User
import os
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

class EnvironmentManager:
    """Manages environment variables in .env file"""
    
    def __init__(self, env_file_path: str = ".env"):
        self.env_file_path = env_file_path
    
    def read_env_file(self) -> Dict[str, str]:
        """Read all environment variables from .env file"""
        env_vars = {}
        
        if not os.path.exists(self.env_file_path):
            return env_vars
        
        try:
            with open(self.env_file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        
        except Exception as e:
            logger.error(f"Error reading .env file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to read environment file: {str(e)}")
        
        return env_vars
    
    def write_env_file(self, env_vars: Dict[str, str]) -> None:
        """Write environment variables to .env file with proper formatting"""
        
        # Read the original file to preserve comments and structure
        original_lines = []
        if os.path.exists(self.env_file_path):
            try:
                with open(self.env_file_path, 'r', encoding='utf-8') as f:
                    original_lines = f.readlines()
            except Exception as e:
                logger.warning(f"Could not read original .env file: {e}")
        
        # Create new content preserving comments and structure
        new_lines = []
        processed_keys = set()
        
        for line in original_lines:
            stripped_line = line.strip()
            
            # Preserve comments and empty lines
            if not stripped_line or stripped_line.startswith('#'):
                new_lines.append(line)
                continue
            
            # Handle environment variables
            if '=' in stripped_line:
                key = stripped_line.split('=', 1)[0].strip()
                if key in env_vars:
                    # Update with new value
                    new_lines.append(f"{key}={env_vars[key]}\n")
                    processed_keys.add(key)
                else:
                    # Keep original line if key not in updates
                    new_lines.append(line)
            else:
                # Keep any other lines as-is
                new_lines.append(line)
        
        # Add any new environment variables that weren't in the original file
        for key, value in env_vars.items():
            if key not in processed_keys:
                new_lines.append(f"{key}={value}\n")
        
        # Write the updated content
        try:
            # Create backup
            if os.path.exists(self.env_file_path):
                backup_path = f"{self.env_file_path}.backup.{int(datetime.now().timestamp())}"
                os.rename(self.env_file_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            with open(self.env_file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            logger.info(f"Successfully updated .env file with {len(env_vars)} variables")
            
        except Exception as e:
            logger.error(f"Error writing .env file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to write environment file: {str(e)}")
    
    def update_env_var(self, key: str, value: str) -> None:
        """Update a single environment variable"""
        env_vars = self.read_env_file()
        env_vars[key] = value
        self.write_env_file(env_vars)
        
        # Update the current process environment
        os.environ[key] = value
    
    def get_env_var(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a single environment variable"""
        env_vars = self.read_env_file()
        return env_vars.get(key, default)
    
    def delete_env_var(self, key: str) -> None:
        """Delete an environment variable"""
        env_vars = self.read_env_file()
        if key in env_vars:
            del env_vars[key]
            self.write_env_file(env_vars)
            
            # Remove from current process environment
            if key in os.environ:
                del os.environ[key]

# Initialize environment manager
env_manager = EnvironmentManager()

@router.get("/environment-variables")
async def get_environment_variables(
    current_user: User = Depends(get_current_superuser)
) -> Dict[str, Any]:
    """Get all environment variables with categorization"""
    
    try:
        env_vars = env_manager.read_env_file()
        
        # Categorize environment variables
        categorized_vars = {
            "database": {},
            "security": {},
            "ai_models": {},
            "data_sharing": {},
            "file_upload": {},
            "storage": {},
            "connectors": {},
            "admin": {},
            "other": {}
        }
        
        # Define categories
        category_mapping = {
            "database": ["DATABASE_URL", "MINDSDB_URL", "MINDSDB_DATABASE", "MINDSDB_USERNAME", "MINDSDB_PASSWORD"],
            "security": ["SECRET_KEY", "ALGORITHM", "ACCESS_TOKEN_EXPIRE_MINUTES", "BACKEND_CORS_ORIGINS"],
            "ai_models": ["GOOGLE_API_KEY", "DEFAULT_GEMINI_MODEL", "GEMINI_ENGINE_NAME", "GEMINI_CHAT_MODEL_NAME", "GEMINI_VISION_MODEL_NAME", "GEMINI_EMBEDDING_MODEL_NAME"],
            "data_sharing": ["ENABLE_DATA_SHARING", "ENABLE_AI_CHAT", "SHARE_LINK_EXPIRY_HOURS", "MAX_CHAT_SESSIONS_PER_DATASET"],
            "file_upload": ["MAX_FILE_SIZE_MB", "ALLOWED_FILE_TYPES", "UPLOAD_PATH", "MAX_DOCUMENT_SIZE_MB", "SUPPORTED_DOCUMENT_TYPES", "DOCUMENT_STORAGE_PATH", "MAX_IMAGE_SIZE_MB", "SUPPORTED_IMAGE_TYPES", "IMAGE_STORAGE_PATH", "ENABLE_IMAGE_PROCESSING", "IMAGE_THUMBNAIL_SIZE"],
            "storage": ["STORAGE_TYPE", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION", "S3_BUCKET_NAME", "S3_COMPATIBLE_ENDPOINT", "S3_COMPATIBLE_ACCESS_KEY", "S3_COMPATIBLE_SECRET_KEY", "S3_COMPATIBLE_BUCKET_NAME", "S3_COMPATIBLE_REGION", "S3_COMPATIBLE_USE_SSL", "S3_COMPATIBLE_ADDRESSING_STYLE"],
            "connectors": ["CONNECTOR_TIMEOUT", "MAX_CONNECTORS_PER_ORG", "ENABLE_S3_CONNECTOR", "ENABLE_DATABASE_CONNECTORS"],
            "admin": ["FIRST_SUPERUSER", "NODE_ENV"]
        }
        
        # Categorize variables
        for key, value in env_vars.items():
            categorized = False
            for category, keys in category_mapping.items():
                if key in keys:
                    categorized_vars[category][key] = {
                        "value": value,
                        "is_sensitive": key in ["SECRET_KEY", "GOOGLE_API_KEY", "MINDSDB_PASSWORD", "AWS_SECRET_ACCESS_KEY", "S3_COMPATIBLE_SECRET_KEY"],
                        "description": get_env_var_description(key)
                    }
                    categorized = True
                    break
            
            if not categorized:
                categorized_vars["other"][key] = {
                    "value": value,
                    "is_sensitive": "KEY" in key.upper() or "PASSWORD" in key.upper() or "SECRET" in key.upper(),
                    "description": "Custom environment variable"
                }
        
        return {
            "categories": categorized_vars,
            "total_variables": len(env_vars),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting environment variables: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/environment-variables/{var_name}")
async def update_environment_variable(
    var_name: str,
    update_data: Dict[str, str],
    current_user: User = Depends(get_current_superuser)
) -> Dict[str, Any]:
    """Update a single environment variable"""
    
    try:
        value = update_data.get("value", "")
        
        # Validate critical variables
        if var_name == "GOOGLE_API_KEY" and value:
            if not value.startswith("AIza") and len(value) < 30:
                raise HTTPException(status_code=400, detail="Invalid Google API key format")
        
        # Update the environment variable
        env_manager.update_env_var(var_name, value)
        
        return {
            "message": f"Environment variable '{var_name}' updated successfully",
            "variable": var_name,
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating environment variable {var_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/environment-variables")
async def create_environment_variable(
    var_data: Dict[str, str],
    current_user: User = Depends(get_current_superuser)
) -> Dict[str, Any]:
    """Create a new environment variable"""
    
    try:
        var_name = var_data.get("name", "").strip().upper()
        var_value = var_data.get("value", "")
        
        if not var_name:
            raise HTTPException(status_code=400, detail="Variable name is required")
        
        # Check if variable already exists
        existing_value = env_manager.get_env_var(var_name)
        if existing_value is not None:
            raise HTTPException(status_code=400, detail=f"Environment variable '{var_name}' already exists")
        
        # Create the environment variable
        env_manager.update_env_var(var_name, var_value)
        
        return {
            "message": f"Environment variable '{var_name}' created successfully",
            "variable": var_name,
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating environment variable: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/environment-variables/{var_name}")
async def delete_environment_variable(
    var_name: str,
    current_user: User = Depends(get_current_superuser)
) -> Dict[str, Any]:
    """Delete an environment variable"""
    
    try:
        # Check if variable exists
        existing_value = env_manager.get_env_var(var_name)
        if existing_value is None:
            raise HTTPException(status_code=404, detail=f"Environment variable '{var_name}' not found")
        
        # Prevent deletion of critical variables
        critical_vars = ["DATABASE_URL", "SECRET_KEY", "ALGORITHM"]
        if var_name in critical_vars:
            raise HTTPException(status_code=400, detail=f"Cannot delete critical environment variable '{var_name}'")
        
        # Delete the environment variable
        env_manager.delete_env_var(var_name)
        
        return {
            "message": f"Environment variable '{var_name}' deleted successfully",
            "variable": var_name,
            "deleted_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error deleting environment variable {var_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/environment-variables/bulk-update")
async def bulk_update_environment_variables(
    updates: Dict[str, str],
    current_user: User = Depends(get_current_superuser)
) -> Dict[str, Any]:
    """Bulk update multiple environment variables"""
    
    try:
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        # Read current environment variables
        current_env = env_manager.read_env_file()
        
        # Apply updates
        updated_vars = []
        for var_name, var_value in updates.items():
            current_env[var_name] = var_value
            updated_vars.append(var_name)
            # Update current process environment
            os.environ[var_name] = var_value
        
        # Write all variables back to file
        env_manager.write_env_file(current_env)
        
        return {
            "message": f"Successfully updated {len(updated_vars)} environment variables",
            "updated_variables": updated_vars,
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error bulk updating environment variables: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/environment-variables/{var_name}")
async def get_environment_variable(
    var_name: str,
    current_user: User = Depends(get_current_superuser)
) -> Dict[str, Any]:
    """Get a specific environment variable"""
    
    try:
        value = env_manager.get_env_var(var_name)
        
        if value is None:
            raise HTTPException(status_code=404, detail=f"Environment variable '{var_name}' not found")
        
        is_sensitive = var_name in ["SECRET_KEY", "GOOGLE_API_KEY", "MINDSDB_PASSWORD", "AWS_SECRET_ACCESS_KEY"]
        
        return {
            "name": var_name,
            "value": "***HIDDEN***" if is_sensitive else value,
            "actual_value": value,
            "is_sensitive": is_sensitive,
            "description": get_env_var_description(var_name)
        }
        
    except Exception as e:
        logger.error(f"Error getting environment variable {var_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/environment-variables/reload")
async def reload_environment_variables(
    current_user: User = Depends(get_current_superuser)
) -> Dict[str, Any]:
    """Reload environment variables from .env files"""
    
    try:
        # Read environment variables from all .env files
        env_files = [
            ".env",
            "backend/.env", 
            "frontend/.env"
        ]
        
        reloaded_vars = {}
        file_results = {}
        
        for env_file in env_files:
            if os.path.exists(env_file):
                try:
                    env_manager_file = EnvironmentManager(env_file)
                    file_vars = env_manager_file.read_env_file()
                    
                    # Update process environment with variables from this file
                    for key, value in file_vars.items():
                        os.environ[key] = value
                        reloaded_vars[key] = value
                    
                    file_results[env_file] = {
                        "status": "success",
                        "variables_count": len(file_vars),
                        "variables": list(file_vars.keys())
                    }
                    
                except Exception as e:
                    file_results[env_file] = {
                        "status": "error",
                        "error": str(e)
                    }
            else:
                file_results[env_file] = {
                    "status": "not_found",
                    "message": "File does not exist"
                }
        
        return {
            "message": f"Successfully reloaded {len(reloaded_vars)} environment variables",
            "total_variables_reloaded": len(reloaded_vars),
            "file_results": file_results,
            "reloaded_variables": list(reloaded_vars.keys()),
            "reloaded_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error reloading environment variables: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_env_var_description(var_name: str) -> str:
    """Get description for environment variables"""
    descriptions = {
        "DATABASE_URL": "Database connection URL",
        "SECRET_KEY": "Secret key for JWT token encryption",
        "ALGORITHM": "Algorithm used for JWT token encryption",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "JWT token expiration time in minutes",
        "BACKEND_CORS_ORIGINS": "Allowed CORS origins for backend API",
        "GOOGLE_API_KEY": "Google API key for Gemini AI integration",
        "MINDSDB_URL": "MindsDB server URL",
        "MINDSDB_DATABASE": "MindsDB database name",
        "MINDSDB_USERNAME": "MindsDB username",
        "MINDSDB_PASSWORD": "MindsDB password",
        "DEFAULT_GEMINI_MODEL": "Default Gemini model to use",
        "GEMINI_ENGINE_NAME": "MindsDB engine name for Gemini",
        "GEMINI_CHAT_MODEL_NAME": "Gemini chat model name",
        "GEMINI_VISION_MODEL_NAME": "Gemini vision model name",
        "GEMINI_EMBEDDING_MODEL_NAME": "Gemini embedding model name",
        "ENABLE_DATA_SHARING": "Enable/disable data sharing features",
        "ENABLE_AI_CHAT": "Enable/disable AI chat functionality",
        "SHARE_LINK_EXPIRY_HOURS": "Default expiry time for share links in hours",
        "MAX_CHAT_SESSIONS_PER_DATASET": "Maximum chat sessions per dataset",
        "MAX_FILE_SIZE_MB": "Maximum file upload size in MB",
        "ALLOWED_FILE_TYPES": "Allowed file types for upload",
        "UPLOAD_PATH": "Path for file uploads",
        "MAX_DOCUMENT_SIZE_MB": "Maximum document size in MB",
        "SUPPORTED_DOCUMENT_TYPES": "Supported document types",
        "DOCUMENT_STORAGE_PATH": "Path for document storage",
        "MAX_IMAGE_SIZE_MB": "Maximum image file size in MB",
        "SUPPORTED_IMAGE_TYPES": "Supported image file types",
        "IMAGE_STORAGE_PATH": "Path for image storage",
        "ENABLE_IMAGE_PROCESSING": "Enable/disable image processing features",
        "IMAGE_THUMBNAIL_SIZE": "Size for generated image thumbnails in pixels",
        "STORAGE_TYPE": "Storage backend type (local, s3, s3_compatible)",
        "AWS_ACCESS_KEY_ID": "AWS access key ID for S3 storage",
        "AWS_SECRET_ACCESS_KEY": "AWS secret access key for S3 storage",
        "AWS_DEFAULT_REGION": "AWS default region for S3 storage",
        "S3_BUCKET_NAME": "AWS S3 bucket name",
        "S3_COMPATIBLE_ENDPOINT": "S3-compatible storage endpoint URL (MinIO, Backblaze, etc.)",
        "S3_COMPATIBLE_ACCESS_KEY": "S3-compatible storage access key",
        "S3_COMPATIBLE_SECRET_KEY": "S3-compatible storage secret key",
        "S3_COMPATIBLE_BUCKET_NAME": "S3-compatible storage bucket name",
        "S3_COMPATIBLE_REGION": "S3-compatible storage region",
        "S3_COMPATIBLE_USE_SSL": "Use SSL for S3-compatible storage connections",
        "S3_COMPATIBLE_ADDRESSING_STYLE": "S3-compatible addressing style (auto, virtual, path)",
        "CONNECTOR_TIMEOUT": "Database connector timeout in seconds",
        "MAX_CONNECTORS_PER_ORG": "Maximum connectors per organization",
        "ENABLE_S3_CONNECTOR": "Enable/disable S3 connector",
        "ENABLE_DATABASE_CONNECTORS": "Enable/disable database connectors",
        "FIRST_SUPERUSER": "First superuser email",
        "NODE_ENV": "Node.js environment (development/production)"
    }
    
    return descriptions.get(var_name, "Custom environment variable")