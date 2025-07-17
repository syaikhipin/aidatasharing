"""
Download Error Handler Service for Enhanced Dataset Management
Provides standardized error handling for download operations
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from app.models.dataset import Dataset, DatasetDownload
from app.models.user import User

logger = logging.getLogger(__name__)


class DownloadErrorHandler:
    """Service for handling download errors with detailed information"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def handle_permission_error(
        self,
        dataset: Optional[Dataset],
        user: Optional[User],
        permission_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle permission-related errors"""
        error_dict = {
            "error_code": "PERMISSION_DENIED",
            "message": permission_details.get("error", "Permission denied"),
            "details": permission_details,
            "recovery_suggestions": [
                "Check if you have the necessary permissions",
                "Contact the dataset owner for access",
                "Verify your organization membership"
            ]
        }
        
        logger.warning(f"Permission error: {error_dict['message']}")
        return error_dict
    
    def handle_file_not_found_error(
        self,
        dataset: Optional[Dataset],
        file_path: Optional[str],
        download_record: Optional[DatasetDownload] = None
    ) -> Dict[str, Any]:
        """Handle file not found errors"""
        error_dict = {
            "error_code": "FILE_NOT_FOUND",
            "message": "The requested file could not be found",
            "details": {
                "dataset_id": dataset.id if dataset else None,
                "file_path": file_path,
                "download_id": download_record.id if download_record else None
            },
            "recovery_suggestions": [
                "Contact the dataset owner",
                "Try downloading again later",
                "Check if the dataset has been updated or deleted"
            ]
        }
        
        logger.error(f"File not found: {file_path}")
        return error_dict
    
    def handle_storage_error(
        self,
        dataset: Dataset,
        storage_error: Exception,
        download_record: Optional[DatasetDownload] = None
    ) -> Dict[str, Any]:
        """Handle storage-related errors"""
        error_dict = {
            "error_code": "STORAGE_ERROR",
            "message": "Storage system error",
            "details": {
                "dataset_id": dataset.id,
                "error": str(storage_error),
                "download_id": download_record.id if download_record else None
            },
            "recovery_suggestions": [
                "Try downloading again later",
                "Contact system administrator",
                "Check system storage capacity"
            ]
        }
        
        logger.error(f"Storage error for dataset {dataset.id}: {storage_error}")
        return error_dict
    
    def handle_file_corruption_error(
        self,
        dataset: Dataset,
        file_path: str,
        corruption_details: Dict[str, Any],
        download_record: Optional[DatasetDownload] = None
    ) -> Dict[str, Any]:
        """Handle file corruption errors"""
        error_dict = {
            "error_code": "FILE_CORRUPTION",
            "message": "The file appears to be corrupted",
            "details": {
                "dataset_id": dataset.id,
                "file_path": file_path,
                "corruption_details": corruption_details,
                "download_id": download_record.id if download_record else None
            },
            "recovery_suggestions": [
                "Contact the dataset owner to re-upload the file",
                "Try downloading in a different format",
                "Check if the dataset has been updated recently"
            ]
        }
        
        logger.error(f"File corruption for dataset {dataset.id}: {corruption_details}")
        return error_dict
    
    def handle_network_error(
        self,
        dataset: Dataset,
        network_error: Exception,
        download_record: Optional[DatasetDownload] = None
    ) -> Dict[str, Any]:
        """Handle network-related errors"""
        error_dict = {
            "error_code": "NETWORK_ERROR",
            "message": "Network error during download",
            "details": {
                "dataset_id": dataset.id,
                "error": str(network_error),
                "download_id": download_record.id if download_record else None,
                "is_resumable": True
            },
            "recovery_suggestions": [
                "Check your network connection",
                "Try downloading again",
                "Use the resumable download feature to continue from where you left off"
            ]
        }
        
        logger.error(f"Network error for dataset {dataset.id}: {network_error}")
        return error_dict
    
    def create_http_exception(self, error_dict: Dict[str, Any]) -> HTTPException:
        """Create HTTPException from error dictionary"""
        # Map error codes to HTTP status codes
        status_code_map = {
            "PERMISSION_DENIED": status.HTTP_403_FORBIDDEN,
            "FILE_NOT_FOUND": status.HTTP_404_NOT_FOUND,
            "STORAGE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "FILE_CORRUPTION": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "NETWORK_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
            "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
            "TOKEN_EXPIRED": status.HTTP_410_GONE,
            "RATE_LIMIT_EXCEEDED": status.HTTP_429_TOO_MANY_REQUESTS
        }
        
        status_code = status_code_map.get(error_dict.get("error_code"), status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return HTTPException(
            status_code=status_code,
            detail=error_dict
        )