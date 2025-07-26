"""
Environment management API endpoints for admin panel
"""
import os
import json
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.auth import get_current_superuser
from app.models.user import User

router = APIRouter()

class EnvironmentVariable(BaseModel):
    key: str
    value: str
    description: str = ""
    category: str = "general"

class EnvironmentUpdate(BaseModel):
    variables: List[EnvironmentVariable]

# Environment variable categories and their descriptions
ENV_CATEGORIES = {
    "database": {
        "name": "Database Configuration",
        "description": "Database connection and settings",
        "variables": ["DATABASE_URL"]
    },
    "security": {
        "name": "Security Configuration", 
        "description": "Authentication and security settings",
        "variables": ["SECRET_KEY", "ALGORITHM", "ACCESS_TOKEN_EXPIRE_MINUTES"]
    },
    "api": {
        "name": "API Configuration",
        "description": "External API keys and endpoints",
        "variables": ["GOOGLE_API_KEY", "MINDSDB_URL", "MINDSDB_DATABASE", "MINDSDB_USERNAME", "MINDSDB_PASSWORD"]
    },
    "ai": {
        "name": "AI Model Configuration",
        "description": "AI model settings and configurations",
        "variables": ["DEFAULT_GEMINI_MODEL", "GEMINI_ENGINE_NAME", "GEMINI_CHAT_MODEL_NAME", "GEMINI_VISION_MODEL_NAME", "GEMINI_EMBEDDING_MODEL_NAME"]
    },
    "sharing": {
        "name": "Data Sharing Configuration",
        "description": "Data sharing and collaboration settings",
        "variables": ["ENABLE_DATA_SHARING", "ENABLE_AI_CHAT", "SHARE_LINK_EXPIRY_HOURS", "MAX_CHAT_SESSIONS_PER_DATASET"]
    },
    "upload": {
        "name": "File Upload Configuration",
        "description": "File upload and processing settings",
        "variables": ["MAX_FILE_SIZE_MB", "ALLOWED_FILE_TYPES", "UPLOAD_PATH", "MAX_DOCUMENT_SIZE_MB", "SUPPORTED_DOCUMENT_TYPES", "DOCUMENT_STORAGE_PATH"]
    },
    "connector": {
        "name": "Data Connector Configuration",
        "description": "Data connector and integration settings",
        "variables": ["CONNECTOR_TIMEOUT", "MAX_CONNECTORS_PER_ORG", "ENABLE_S3_CONNECTOR", "ENABLE_DATABASE_CONNECTORS"]
    },
    "aws": {
        "name": "AWS Configuration",
        "description": "AWS S3 and cloud service settings",
        "variables": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION", "S3_BUCKET_NAME"]
    },
    "admin": {
        "name": "Admin Configuration",
        "description": "Administrator account settings",
        "variables": ["FIRST_SUPERUSER", "FIRST_SUPERUSER_PASSWORD"]
    },
    "system": {
        "name": "System Configuration",
        "description": "System-wide settings",
        "variables": ["NODE_ENV", "BACKEND_CORS_ORIGINS"]
    }
}

def get_env_file_path():
    """Get the path to the unified .env file"""
    # Go up one directory from backend to project root
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", ".env")

def read_env_file() -> Dict[str, str]:
    """Read environment variables from .env file"""
    env_path = get_env_file_path()
    env_vars = {}
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    
    return env_vars

def write_env_file(env_vars: Dict[str, str]):
    """Write environment variables to .env file"""
    env_path = get_env_file_path()
    
    # Read existing file to preserve comments and structure
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    
    # Update existing variables or add new ones
    updated_lines = []
    updated_keys = set()
    
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0]
            if key in env_vars:
                updated_lines.append(f"{key}={env_vars[key]}\n")
                updated_keys.add(key)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # Add new variables that weren't in the file
    for key, value in env_vars.items():
        if key not in updated_keys:
            updated_lines.append(f"{key}={value}\n")
    
    # Write back to file
    with open(env_path, 'w') as f:
        f.writelines(updated_lines)

@router.get("/")
async def get_environment_variables(
    current_user: User = Depends(get_current_superuser)
):
    """Get all environment variables organized by category"""
    try:
        env_vars = read_env_file()
        
        # Organize by category
        categorized_vars = {}
        for category_key, category_info in ENV_CATEGORIES.items():
            categorized_vars[category_key] = {
                "name": category_info["name"],
                "description": category_info["description"],
                "variables": []
            }
            
            for var_key in category_info["variables"]:
                categorized_vars[category_key]["variables"].append({
                    "key": var_key,
                    "value": env_vars.get(var_key, ""),
                    "description": get_variable_description(var_key)
                })
        
        return {
            "categories": categorized_vars,
            "total_variables": len(env_vars)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read environment variables: {str(e)}"
        )

@router.put("/")
async def update_environment_variables(
    update: EnvironmentUpdate,
    current_user: User = Depends(get_current_superuser)
):
    """Update environment variables"""
    try:
        # Read current environment
        current_env = read_env_file()
        
        # Update with new values
        for var in update.variables:
            current_env[var.key] = var.value
        
        # Write back to file
        write_env_file(current_env)
        
        return {
            "message": "Environment variables updated successfully",
            "updated_count": len(update.variables)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update environment variables: {str(e)}"
        )

@router.post("/variable")
async def create_environment_variable(
    variable: EnvironmentVariable,
    current_user: User = Depends(get_current_superuser)
):
    """Create a new environment variable"""
    try:
        env_vars = read_env_file()
        env_vars[variable.key] = variable.value
        write_env_file(env_vars)
        
        return {
            "message": f"Environment variable '{variable.key}' created successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create environment variable: {str(e)}"
        )

@router.delete("/variable/{key}")
async def delete_environment_variable(
    key: str,
    current_user: User = Depends(get_current_superuser)
):
    """Delete an environment variable"""
    try:
        env_vars = read_env_file()
        if key in env_vars:
            del env_vars[key]
            write_env_file(env_vars)
            return {"message": f"Environment variable '{key}' deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Environment variable '{key}' not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete environment variable: {str(e)}"
        )

@router.post("/reload")
async def reload_environment(
    current_user: User = Depends(get_current_superuser)
):
    """Reload environment variables (requires application restart for full effect)"""
    try:
        env_vars = read_env_file()
        
        # Update os.environ with new values
        for key, value in env_vars.items():
            os.environ[key] = value
        
        return {
            "message": "Environment variables reloaded successfully",
            "note": "Some changes may require application restart to take full effect"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload environment variables: {str(e)}"
        )

def get_variable_description(key: str) -> str:
    """Get description for environment variable"""
    descriptions = {
        "DATABASE_URL": "SQLite database connection string",
        "SECRET_KEY": "JWT signing secret key",
        "ALGORITHM": "JWT algorithm (HS256)",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "JWT token expiration time in minutes",
        "BACKEND_CORS_ORIGINS": "Comma-separated list of allowed CORS origins",
        "GOOGLE_API_KEY": "Google AI API key for Gemini models",
        "MINDSDB_URL": "MindsDB server URL",
        "MINDSDB_DATABASE": "MindsDB database name",
        "MINDSDB_USERNAME": "MindsDB username (optional)",
        "MINDSDB_PASSWORD": "MindsDB password (optional)",
        "DEFAULT_GEMINI_MODEL": "Default Gemini model to use",
        "GEMINI_ENGINE_NAME": "Gemini engine name in MindsDB",
        "GEMINI_CHAT_MODEL_NAME": "Gemini chat model name",
        "GEMINI_VISION_MODEL_NAME": "Gemini vision model name",
        "GEMINI_EMBEDDING_MODEL_NAME": "Gemini embedding model name",
        "ENABLE_DATA_SHARING": "Enable data sharing features",
        "ENABLE_AI_CHAT": "Enable AI chat functionality",
        "SHARE_LINK_EXPIRY_HOURS": "Share link expiration time in hours",
        "MAX_CHAT_SESSIONS_PER_DATASET": "Maximum chat sessions per dataset",
        "MAX_FILE_SIZE_MB": "Maximum file upload size in MB",
        "ALLOWED_FILE_TYPES": "Comma-separated list of allowed file types",
        "UPLOAD_PATH": "File upload storage path",
        "MAX_DOCUMENT_SIZE_MB": "Maximum document size in MB",
        "SUPPORTED_DOCUMENT_TYPES": "Comma-separated list of supported document types",
        "DOCUMENT_STORAGE_PATH": "Document storage path",
        "CONNECTOR_TIMEOUT": "Data connector timeout in seconds",
        "MAX_CONNECTORS_PER_ORG": "Maximum connectors per organization",
        "ENABLE_S3_CONNECTOR": "Enable S3 connector",
        "ENABLE_DATABASE_CONNECTORS": "Enable database connectors",
        "AWS_ACCESS_KEY_ID": "AWS access key ID for S3",
        "AWS_SECRET_ACCESS_KEY": "AWS secret access key for S3",
        "AWS_DEFAULT_REGION": "AWS default region",
        "S3_BUCKET_NAME": "S3 bucket name",
        "FIRST_SUPERUSER": "Default admin user email",
        "FIRST_SUPERUSER_PASSWORD": "Default admin user password",
        "NODE_ENV": "Node.js environment (development/production)"
    }
    return descriptions.get(key, "No description available")