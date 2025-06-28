"""
MindsDB File Handler Service
Handles file uploads, processing, and integration with MindsDB
"""

import os
import hashlib
import mimetypes
from typing import Dict, List, Optional, Any, BinaryIO
from sqlalchemy.orm import Session
from fastapi import UploadFile
import logging
from datetime import datetime

from app.models.file_handler import FileUpload, MindsDBHandler, FileProcessingLog, UploadStatus, ProcessingStatus
from app.models.dataset import Dataset
from app.models.user import User
from app.services.mindsdb import MindsDBService
from app.core.config import settings

logger = logging.getLogger(__name__)


class FileHandlerService:
    """Service for handling file uploads and MindsDB integration"""
    
    def __init__(self, db: Session):
        self.db = db
        self.mindsdb_service = MindsDBService()
        self.upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
        
        # Ensure upload directory exists
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def get_file_mime_type(self, filename: str) -> Optional[str]:
        """Get MIME type for file"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type
    
    def save_uploaded_file(self, file: UploadFile, user: User, dataset: Dataset) -> FileUpload:
        """Save uploaded file and create tracking record"""
        try:
            # Read file content
            file_content = file.file.read()
            file_size = len(file_content)
            file_hash = self.calculate_file_hash(file_content)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{user.id}_{file.filename}"
            file_path = os.path.join(self.upload_dir, safe_filename)
            
            # Save file to disk
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # Create tracking record
            file_upload = FileUpload(
                dataset_id=dataset.id,
                user_id=user.id,
                organization_id=user.organization_id,
                original_filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                file_hash=file_hash,
                mime_type=self.get_file_mime_type(file.filename),
                upload_status=UploadStatus.UPLOADED
            )
            
            self.db.add(file_upload)
            self.db.commit()
            self.db.refresh(file_upload)
            
            # Log the upload
            self.log_processing_step(
                file_upload.id,
                "file_upload",
                "completed",
                f"File uploaded successfully: {file.filename}",
                {"file_size": file_size, "file_hash": file_hash}
            )
            
            logger.info(f"File uploaded successfully: {file.filename} -> {safe_filename}")
            return file_upload
            
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            raise
    
    def process_file_with_mindsdb(self, file_upload: FileUpload) -> Dict[str, Any]:
        """Process uploaded file with MindsDB"""
        try:
            # Update status to processing
            file_upload.upload_status = UploadStatus.PROCESSING
            file_upload.processing_started_at = datetime.utcnow()
            self.db.commit()
            
            self.log_processing_step(
                file_upload.id,
                "mindsdb_processing",
                "started",
                "Starting MindsDB file processing"
            )
            
            # Create file handler in MindsDB
            handler_result = self.create_mindsdb_file_handler(file_upload)
            
            if handler_result["success"]:
                # Upload file to MindsDB
                upload_result = self.upload_file_to_mindsdb(file_upload)
                
                if upload_result["success"]:
                    # Update status to completed
                    file_upload.upload_status = UploadStatus.COMPLETED
                    file_upload.processing_completed_at = datetime.utcnow()
                    file_upload.mindsdb_file_id = upload_result.get("file_id")
                    
                    self.log_processing_step(
                        file_upload.id,
                        "mindsdb_processing",
                        "completed",
                        "File processing completed successfully",
                        upload_result
                    )
                    
                    result = {
                        "success": True,
                        "message": "File processed successfully",
                        "file_id": upload_result.get("file_id"),
                        "mindsdb_handler": handler_result.get("handler_name")
                    }
                else:
                    # Processing failed
                    file_upload.upload_status = UploadStatus.FAILED
                    file_upload.error_message = upload_result.get("error", "Unknown error")
                    
                    self.log_processing_step(
                        file_upload.id,
                        "mindsdb_processing",
                        "failed",
                        f"File processing failed: {upload_result.get('error')}",
                        upload_result
                    )
                    
                    result = {
                        "success": False,
                        "error": upload_result.get("error", "File processing failed")
                    }
            else:
                # Handler creation failed
                file_upload.upload_status = UploadStatus.FAILED
                file_upload.error_message = handler_result.get("error", "Handler creation failed")
                
                self.log_processing_step(
                    file_upload.id,
                    "handler_creation",
                    "failed",
                    f"Handler creation failed: {handler_result.get('error')}",
                    handler_result
                )
                
                result = {
                    "success": False,
                    "error": handler_result.get("error", "Handler creation failed")
                }
            
            self.db.commit()
            return result
            
        except Exception as e:
            # Processing failed with exception
            file_upload.upload_status = UploadStatus.FAILED
            file_upload.error_message = str(e)
            self.db.commit()
            
            self.log_processing_step(
                file_upload.id,
                "mindsdb_processing",
                "failed",
                f"Processing failed with exception: {str(e)}"
            )
            
            logger.error(f"MindsDB file processing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_mindsdb_file_handler(self, file_upload: FileUpload) -> Dict[str, Any]:
        """Create file handler in MindsDB"""
        try:
            handler_name = f"file_handler_{file_upload.id}"
            
            # Check if handler already exists
            existing_handler = self.db.query(MindsDBHandler).filter(
                MindsDBHandler.organization_id == file_upload.organization_id,
                MindsDBHandler.handler_name == handler_name
            ).first()
            
            if existing_handler:
                return {
                    "success": True,
                    "handler_name": handler_name,
                    "message": "Handler already exists"
                }
            
            # Create file handler in MindsDB
            create_query = f"""
            CREATE DATABASE {handler_name}
            WITH ENGINE = 'files'
            """
            
            result = self.mindsdb_service.execute_query(create_query)
            
            if result.get("error"):
                return {
                    "success": False,
                    "error": f"Failed to create MindsDB handler: {result.get('error')}"
                }
            
            # Save handler configuration
            handler_config = MindsDBHandler(
                organization_id=file_upload.organization_id,
                handler_name=handler_name,
                handler_type="file",
                configuration={
                    "engine": "files",
                    "file_upload_id": file_upload.id,
                    "original_filename": file_upload.original_filename
                }
            )
            
            self.db.add(handler_config)
            self.db.commit()
            
            return {
                "success": True,
                "handler_name": handler_name,
                "message": "Handler created successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to create MindsDB file handler: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def upload_file_to_mindsdb(self, file_upload: FileUpload) -> Dict[str, Any]:
        """Upload file to MindsDB for processing"""
        try:
            # For now, we'll create a table reference to the file
            # In a full implementation, you'd use MindsDB's file upload API
            
            handler_name = f"file_handler_{file_upload.id}"
            table_name = f"uploaded_file_{file_upload.id}"
            
            # Create table reference to the uploaded file
            create_table_query = f"""
            CREATE TABLE {handler_name}.{table_name} (
                file_path '{file_upload.file_path}'
            )
            """
            
            result = self.mindsdb_service.execute_query(create_table_query)
            
            if result.get("error"):
                return {
                    "success": False,
                    "error": f"Failed to create file table: {result.get('error')}"
                }
            
            return {
                "success": True,
                "file_id": table_name,
                "handler": handler_name,
                "message": "File uploaded to MindsDB successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to upload file to MindsDB: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def log_processing_step(
        self,
        file_upload_id: int,
        step: str,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[int] = None
    ):
        """Log a processing step"""
        try:
            log_entry = FileProcessingLog(
                file_upload_id=file_upload_id,
                step=step,
                status=status,
                message=message,
                details=details,
                processing_time_ms=processing_time_ms
            )
            
            self.db.add(log_entry)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log processing step: {str(e)}")
    
    def get_file_upload_status(self, file_upload_id: int) -> Optional[Dict[str, Any]]:
        """Get file upload status and processing logs"""
        file_upload = self.db.query(FileUpload).filter(
            FileUpload.id == file_upload_id
        ).first()
        
        if not file_upload:
            return None
        
        # Get processing logs
        logs = self.db.query(FileProcessingLog).filter(
            FileProcessingLog.file_upload_id == file_upload_id
        ).order_by(FileProcessingLog.created_at).all()
        
        return {
            "id": file_upload.id,
            "original_filename": file_upload.original_filename,
            "file_size": file_upload.file_size,
            "upload_status": file_upload.upload_status,
            "mindsdb_file_id": file_upload.mindsdb_file_id,
            "processing_started_at": file_upload.processing_started_at,
            "processing_completed_at": file_upload.processing_completed_at,
            "error_message": file_upload.error_message,
            "created_at": file_upload.created_at,
            "processing_logs": [
                {
                    "step": log.step,
                    "status": log.status,
                    "message": log.message,
                    "details": log.details,
                    "processing_time_ms": log.processing_time_ms,
                    "created_at": log.created_at
                }
                for log in logs
            ]
        }
    
    def get_organization_handlers(self, organization_id: int) -> List[Dict[str, Any]]:
        """Get all MindsDB handlers for an organization"""
        handlers = self.db.query(MindsDBHandler).filter(
            MindsDBHandler.organization_id == organization_id,
            MindsDBHandler.is_active == True
        ).all()
        
        return [
            {
                "id": handler.id,
                "handler_name": handler.handler_name,
                "handler_type": handler.handler_type,
                "configuration": handler.configuration,
                "created_at": handler.created_at,
                "updated_at": handler.updated_at
            }
            for handler in handlers
        ] 