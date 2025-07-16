"""
Download Validator Service for Enhanced Dataset Management
Provides comprehensive validation and error handling for download operations
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.dataset import Dataset, DatasetDownload
from app.models.organization import Organization
from app.services.data_sharing import DataSharingService
import logging

logger = logging.getLogger(__name__)


class DownloadValidationError(Exception):
    """Custom exception for download validation errors"""
    def __init__(self, message: str, error_code: str, details: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class DownloadValidator:
    """Service for validating download requests and providing detailed error information"""
    
    def __init__(self, db: Session):
        self.db = db
        self.data_sharing_service = DataSharingService(db)
    
    def validate_download_request(
        self,
        dataset_id: int,
        user: User,
        file_format: str = "original",
        compression: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Comprehensive validation of download request
        
        Returns:
            Tuple of (is_valid, error_details)
        """
        try:
            # Step 1: Dataset existence validation
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                return False, {
                    "error_code": "DATASET_NOT_FOUND",
                    "message": "Dataset not found",
                    "details": {"dataset_id": dataset_id}
                }
            
            # Step 2: Dataset status validation
            if dataset.is_deleted:
                return False, {
                    "error_code": "DATASET_DELETED",
                    "message": "Dataset has been deleted",
                    "details": {
                        "dataset_id": dataset_id,
                        "deleted_at": dataset.deleted_at.isoformat() if dataset.deleted_at else None
                    }
                }
            
            if not dataset.is_active:
                return False, {
                    "error_code": "DATASET_INACTIVE",
                    "message": "Dataset is currently inactive",
                    "details": {"dataset_id": dataset_id, "status": dataset.status.value}
                }
            
            # Step 3: Basic access validation
            if not self.data_sharing_service.can_access_dataset(user, dataset):
                return False, {
                    "error_code": "ACCESS_DENIED",
                    "message": "Access denied to this dataset",
                    "details": {
                        "dataset_id": dataset_id,
                        "sharing_level": dataset.sharing_level.value,
                        "user_organization": user.organization_id,
                        "dataset_organization": dataset.organization_id,
                        "required_permissions": self._get_required_permissions(dataset)
                    }
                }
            
            # Step 4: Download permission validation
            if not self.data_sharing_service.can_download_dataset(user, dataset):
                return False, {
                    "error_code": "DOWNLOAD_PERMISSION_DENIED",
                    "message": "Download permission denied for this dataset",
                    "details": {
                        "dataset_id": dataset_id,
                        "user_role": user.role,
                        "dataset_download_enabled": dataset.allow_download,
                        "organization_policy": self._get_organization_download_summary(user.organization_id),
                        "user_permissions": self._get_user_download_summary(user)
                    }
                }
            
            # Step 5: Rate limit validation
            rate_limit_check = self.data_sharing_service.check_download_rate_limit(user)
            if not rate_limit_check.get("allowed", True):
                return False, {
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": "Download rate limit exceeded",
                    "details": {
                        "daily_limit": rate_limit_check.get("daily_limit"),
                        "daily_used": rate_limit_check.get("daily_used"),
                        "hourly_limit": rate_limit_check.get("hourly_limit"),
                        "hourly_used": rate_limit_check.get("hourly_used"),
                        "reset_time": rate_limit_check.get("reset_time"),
                        "retry_after": self._calculate_retry_after(rate_limit_check)
                    }
                }
            
            # Step 6: File format validation
            format_validation = self._validate_file_format(user, dataset, file_format)
            if not format_validation["valid"]:
                return False, {
                    "error_code": "INVALID_FILE_FORMAT",
                    "message": format_validation["message"],
                    "details": format_validation["details"]
                }
            
            # Step 7: File size validation
            size_validation = self._validate_file_size(user, dataset)
            if not size_validation["valid"]:
                return False, {
                    "error_code": "FILE_SIZE_EXCEEDED",
                    "message": size_validation["message"],
                    "details": size_validation["details"]
                }
            
            # Step 8: Compression validation
            if compression:
                compression_validation = self._validate_compression(user, compression)
                if not compression_validation["valid"]:
                    return False, {
                        "error_code": "INVALID_COMPRESSION",
                        "message": compression_validation["message"],
                        "details": compression_validation["details"]
                    }
            
            # All validations passed
            return True, None
            
        except Exception as e:
            logger.error(f"❌ Download validation failed: {e}")
            return False, {
                "error_code": "VALIDATION_ERROR",
                "message": "Internal validation error",
                "details": {"error": str(e)}
            }
    
    def _get_required_permissions(self, dataset: Dataset) -> Dict[str, Any]:
        """Get required permissions for dataset access"""
        return {
            "organization_membership": True,
            "sharing_level": dataset.sharing_level.value,
            "department_membership": dataset.sharing_level.value == "department",
            "owner_access": dataset.sharing_level.value == "private"
        }
    
    def _get_organization_download_summary(self, organization_id: int) -> Dict[str, Any]:
        """Get summary of organization download policy"""
        try:
            policy = self.data_sharing_service._get_organization_download_policy(organization_id)
            return {
                "downloads_restricted": policy.get("restrict_downloads", False),
                "approval_required": policy.get("require_approval", False),
                "allowed_file_types": policy.get("allowed_file_types", []),
                "max_file_size_mb": policy.get("max_file_size_mb", 1000),
                "rate_limit_per_hour": policy.get("rate_limit_per_hour", 50)
            }
        except Exception:
            return {"error": "Could not retrieve organization policy"}
    
    def _get_user_download_summary(self, user: User) -> Dict[str, Any]:
        """Get summary of user download permissions"""
        try:
            permissions = self.data_sharing_service._get_user_download_permissions(user)
            return {
                "role": user.role,
                "download_restricted": permissions.get("download_restricted", False),
                "max_downloads_per_day": permissions.get("max_downloads_per_day", 100),
                "allowed_file_types": permissions.get("allowed_file_types", [])
            }
        except Exception:
            return {"error": "Could not retrieve user permissions"}
    
    def _validate_file_format(self, user: User, dataset: Dataset, file_format: str) -> Dict[str, Any]:
        """
        Validate requested file format based on dataset type (uploaded file or connector)
        """
        try:
            user_permissions = self.data_sharing_service._get_user_download_permissions(user)
            allowed_formats = user_permissions.get("allowed_file_types", ["csv", "json", "excel", "pdf"])
            
            # Original format is always allowed if user can download
            if file_format == "original":
                return {"valid": True}
            
            # Check if requested format is allowed for the user's role
            if file_format not in allowed_formats:
                return {
                    "valid": False,
                    "message": f"File format '{file_format}' not allowed for your role",
                    "details": {
                        "requested_format": file_format,
                        "allowed_formats": allowed_formats,
                        "user_role": user.role
                    }
                }
            
            # Determine if this is an uploaded file or connector-based dataset
            is_connector_dataset = dataset.connector_id is not None
            dataset_type = dataset.type.value.lower()
            
            # Different validation logic based on dataset source
            if is_connector_dataset:
                # For connector-based datasets (database, API, etc.)
                connector_type = dataset.connector.connector_type if dataset.connector else "unknown"
                
                # Define format compatibility for connector types
                connector_compatibility = {
                    "mysql": ["csv", "json", "excel"],
                    "postgresql": ["csv", "json", "excel"],
                    "s3": ["csv", "json", "excel", "parquet"],
                    "api": ["json", "csv"],
                    "mongodb": ["json", "csv"],
                    "snowflake": ["csv", "json", "parquet"],
                    "bigquery": ["csv", "json"],
                    "redshift": ["csv", "json"]
                }
                
                compatible_formats = connector_compatibility.get(connector_type, ["csv", "json"])
                
                if file_format not in compatible_formats:
                    return {
                        "valid": False,
                        "message": f"Cannot convert {connector_type} connector data to {file_format} format",
                        "details": {
                            "connector_type": connector_type,
                            "requested_format": file_format,
                            "compatible_formats": compatible_formats
                        }
                    }
            else:
                # For uploaded file datasets
                file_compatibility = {
                    "csv": ["csv", "excel", "json"],
                    "json": ["json", "csv"],
                    "excel": ["excel", "csv", "json"],
                    "pdf": ["pdf"],
                    "parquet": ["parquet", "csv", "json"],
                    "s3_bucket": ["csv", "json", "parquet", "excel"]
                }
                
                compatible_formats = file_compatibility.get(dataset_type, [])
                if file_format not in compatible_formats and file_format != "original":
                    return {
                        "valid": False,
                        "message": f"Cannot convert {dataset_type} dataset to {file_format} format",
                        "details": {
                            "dataset_type": dataset_type,
                            "requested_format": file_format,
                            "compatible_formats": compatible_formats
                        }
                    }
            
            return {"valid": True}
            
        except Exception as e:
            logger.error(f"File format validation error: {e}")
            return {
                "valid": False,
                "message": "File format validation error",
                "details": {"error": str(e)}
            }
    
    def _validate_file_size(self, user: User, dataset: Dataset) -> Dict[str, Any]:
        """Validate file size against user and organization limits"""
        try:
            org_policy = self.data_sharing_service._get_organization_download_policy(user.organization_id)
            max_size_mb = org_policy.get("max_file_size_mb", 1000)
            
            if dataset.size_bytes:
                file_size_mb = dataset.size_bytes / (1024 * 1024)
                
                if file_size_mb > max_size_mb:
                    return {
                        "valid": False,
                        "message": f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)",
                        "details": {
                            "file_size_mb": round(file_size_mb, 1),
                            "max_allowed_mb": max_size_mb,
                            "user_role": user.role
                        }
                    }
            
            return {"valid": True}
            
        except Exception as e:
            return {
                "valid": False,
                "message": "File size validation error",
                "details": {"error": str(e)}
            }
    
    def _validate_compression(self, user: User, compression: str) -> Dict[str, Any]:
        """Validate compression type"""
        try:
            org_policy = self.data_sharing_service._get_organization_download_policy(user.organization_id)
            
            if not org_policy.get("allow_compression", True):
                return {
                    "valid": False,
                    "message": "Compression not allowed by organization policy",
                    "details": {"requested_compression": compression}
                }
            
            allowed_compression = org_policy.get("allowed_compression_types", ["none", "zip", "gzip"])
            
            if compression not in allowed_compression:
                return {
                    "valid": False,
                    "message": f"Compression type '{compression}' not allowed",
                    "details": {
                        "requested_compression": compression,
                        "allowed_types": allowed_compression
                    }
                }
            
            return {"valid": True}
            
        except Exception as e:
            return {
                "valid": False,
                "message": "Compression validation error",
                "details": {"error": str(e)}
            }
    
    def _calculate_retry_after(self, rate_limit_info: Dict[str, Any]) -> int:
        """Calculate retry-after time in seconds"""
        try:
            # If hourly limit exceeded, retry after next hour
            if rate_limit_info.get("hourly_used", 0) >= rate_limit_info.get("hourly_limit", 50):
                current_hour = datetime.utcnow().hour
                next_hour = datetime.utcnow().replace(hour=(current_hour + 1) % 24, minute=0, second=0, microsecond=0)
                if next_hour <= datetime.utcnow():
                    next_hour += timedelta(days=1)
                return int((next_hour - datetime.utcnow()).total_seconds())
            
            # If daily limit exceeded, retry after next day
            if rate_limit_info.get("daily_used", 0) >= rate_limit_info.get("daily_limit", 100):
                next_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                return int((next_day - datetime.utcnow()).total_seconds())
            
            return 3600  # Default: retry after 1 hour
            
        except Exception:
            return 3600
    
    def get_download_requirements(self, dataset_id: int, user: User) -> Dict[str, Any]:
        """Get download requirements and user capabilities for a dataset"""
        try:
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                return {"error": "Dataset not found"}
            
            # Get user permissions and organization policy
            user_permissions = self.data_sharing_service._get_user_download_permissions(user)
            org_policy = self.data_sharing_service._get_organization_download_policy(user.organization_id)
            rate_limit_status = self.data_sharing_service.check_download_rate_limit(user)
            
            # Determine dataset source type and available formats
            is_connector_dataset = dataset.connector_id is not None
            dataset_type = dataset.type.value.lower()
            
            # Get available formats based on dataset type
            available_formats = ["original"]
            if is_connector_dataset:
                connector_type = dataset.connector.connector_type if dataset.connector else "unknown"
                connector_compatibility = {
                    "mysql": ["csv", "json", "excel"],
                    "postgresql": ["csv", "json", "excel"],
                    "s3": ["csv", "json", "excel", "parquet"],
                    "api": ["json", "csv"],
                    "mongodb": ["json", "csv"],
                    "snowflake": ["csv", "json", "parquet"],
                    "bigquery": ["csv", "json"],
                    "redshift": ["csv", "json"]
                }
                available_formats.extend(connector_compatibility.get(connector_type, ["csv", "json"]))
            else:
                file_compatibility = {
                    "csv": ["csv", "excel", "json"],
                    "json": ["json", "csv"],
                    "excel": ["excel", "csv", "json"],
                    "pdf": ["pdf"],
                    "parquet": ["parquet", "csv", "json"],
                    "s3_bucket": ["csv", "json", "parquet", "excel"]
                }
                available_formats.extend(file_compatibility.get(dataset_type, []))
            
            # Filter available formats by user permissions
            allowed_formats = user_permissions.get("allowed_file_types", ["csv", "json", "excel", "pdf"])
            available_formats = list(set(available_formats))  # Remove duplicates
            allowed_available_formats = [fmt for fmt in available_formats if fmt == "original" or fmt in allowed_formats]
            
            # Get connector details if applicable
            connector_details = None
            if is_connector_dataset and dataset.connector:
                connector = dataset.connector
                connector_details = {
                    "id": connector.id,
                    "name": connector.name,
                    "type": connector.connector_type,
                    "mindsdb_database": connector.mindsdb_database_name
                }
            
            return {
                "dataset_info": {
                    "id": dataset.id,
                    "name": dataset.name,
                    "type": dataset.type.value,
                    "size_bytes": dataset.size_bytes,
                    "size_mb": round(dataset.size_bytes / (1024 * 1024), 1) if dataset.size_bytes else None,
                    "sharing_level": dataset.sharing_level.value,
                    "download_enabled": dataset.allow_download,
                    "source_type": "connector" if is_connector_dataset else "uploaded_file",
                    "connector": connector_details,
                    "mindsdb_table": dataset.mindsdb_table_name
                },
                "download_options": {
                    "available_formats": allowed_available_formats,
                    "recommended_format": self._get_recommended_format(dataset),
                    "supports_compression": org_policy.get("allow_compression", True),
                    "allowed_compression_types": org_policy.get("allowed_compression_types", ["none", "zip", "gzip"]) if org_policy.get("allow_compression", True) else []
                },
                "user_capabilities": {
                    "can_access": self.data_sharing_service.can_access_dataset(user, dataset),
                    "can_download": self.data_sharing_service.can_download_dataset(user, dataset),
                    "role": user.role,
                    "max_downloads_per_day": user_permissions.get("max_downloads_per_day"),
                    "allowed_file_types": user_permissions.get("allowed_file_types")
                },
                "rate_limits": {
                    "daily_limit": rate_limit_status.get("daily_limit"),
                    "daily_used": rate_limit_status.get("daily_used"),
                    "daily_remaining": rate_limit_status.get("daily_limit", 0) - rate_limit_status.get("daily_used", 0),
                    "hourly_limit": rate_limit_status.get("hourly_limit"),
                    "hourly_used": rate_limit_status.get("hourly_used"),
                    "hourly_remaining": rate_limit_status.get("hourly_limit", 0) - rate_limit_status.get("hourly_used", 0)
                },
                "organization_policy": {
                    "max_file_size_mb": org_policy.get("max_file_size_mb"),
                    "allowed_file_types": org_policy.get("allowed_file_types"),
                    "compression_allowed": org_policy.get("allow_compression"),
                    "allowed_compression_types": org_policy.get("allowed_compression_types")
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get download requirements: {e}")
            return {"error": str(e)}
    
    def _get_recommended_format(self, dataset: Dataset) -> str:
        """Get recommended download format based on dataset type"""
        is_connector_dataset = dataset.connector_id is not None
        dataset_type = dataset.type.value.lower()
        
        if is_connector_dataset:
            # For connector datasets, CSV is usually a safe default
            return "csv"
        else:
            # For uploaded files, recommend the original format
            return "original"