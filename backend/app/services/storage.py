"""
Storage Service
Handles file storage operations for datasets
"""

import os
import hashlib
import uuid
import secrets
import mimetypes
from typing import Dict, Any, Optional, BinaryIO, AsyncGenerator
from datetime import datetime, timedelta
import logging
from fastapi import UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse, FileResponse
import aiofiles
import asyncio

logger = logging.getLogger(__name__)

class StorageService:
    """Service for handling file storage operations"""
    
    def __init__(self):
        # Define storage directory relative to this file
        self.storage_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage")
        
        # Ensure storage directory exists
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Define chunk size for streaming (8MB)
        self.chunk_size = 8 * 1024 * 1024
    
    async def store_dataset_file(
        self,
        file_content: bytes,
        original_filename: str,
        dataset_id: int,
        organization_id: int
    ) -> Dict[str, Any]:
        """
        Store a dataset file in the storage system
        
        Args:
            file_content: The binary content of the file
            original_filename: The original filename
            dataset_id: The ID of the dataset
            organization_id: The ID of the organization
            
        Returns:
            Dict with storage information
        """
        try:
            # Create organization directory if it doesn't exist
            org_dir = os.path.join(self.storage_dir, f"org_{organization_id}")
            os.makedirs(org_dir, exist_ok=True)
            
            # Generate a unique filename
            file_hash = hashlib.sha256(file_content).hexdigest()[:16]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = original_filename.split('.')[-1] if '.' in original_filename else ''
            
            safe_filename = f"dataset_{dataset_id}_{timestamp}_{file_hash}.{extension}"
            file_path = os.path.join(org_dir, safe_filename)
            
            # Save the file
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # Return storage information
            relative_path = os.path.join(f"org_{organization_id}", safe_filename)
            
            logger.info(f"File stored successfully: {original_filename} -> {safe_filename}")
            
            return {
                "success": True,
                "filename": safe_filename,
                "original_filename": original_filename,
                "file_path": file_path,
                "relative_path": relative_path,
                "file_size": len(file_content),
                "file_hash": file_hash
            }
            
        except Exception as e:
            logger.error(f"File storage failed: {str(e)}")
            raise
    
    async def retrieve_dataset_file(self, file_path: str) -> Optional[str]:
        """
        Retrieve a dataset file from storage
        
        Args:
            file_path: The path to the file
            
        Returns:
            The full path to the file if it exists, None otherwise
        """
        # Check if path is relative or absolute
        if not os.path.isabs(file_path):
            full_path = os.path.join(self.storage_dir, file_path)
        else:
            full_path = file_path
        
        if os.path.exists(full_path):
            return full_path
        
        return None
    
    async def delete_dataset_file(self, file_path: str) -> bool:
        """
        Delete a dataset file from storage
        
        Args:
            file_path: The path to the file
            
        Returns:
            True if the file was deleted, False otherwise
        """
        try:
            # Check if path is relative or absolute
            if not os.path.isabs(file_path):
                full_path = os.path.join(self.storage_dir, file_path)
            else:
                full_path = file_path
            
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.info(f"File deleted successfully: {file_path}")
                return True
            
            logger.warning(f"File not found for deletion: {file_path}")
            return False
            
        except Exception as e:
            logger.error(f"File deletion failed: {str(e)}")
            return False
    
    def generate_download_token(self, dataset_id: int, user_id: Optional[int] = None, expires_in_hours: int = 24) -> str:
        """
        Generate a secure download token for a dataset
        
        Args:
            dataset_id: Dataset ID
            user_id: User ID (optional)
            expires_in_hours: Token expiration in hours
            
        Returns:
            Secure download token
        """
        # Generate a random token with dataset ID and timestamp
        random_part = secrets.token_urlsafe(16)
        timestamp = int(datetime.now().timestamp())
        
        # Combine parts with dataset ID and user ID (if provided)
        token_parts = [random_part, str(dataset_id), str(timestamp)]
        if user_id:
            token_parts.append(str(user_id))
        
        # Join parts and hash
        token_base = "_".join(token_parts)
        token_hash = hashlib.sha256(token_base.encode()).hexdigest()[:32]
        
        # Final token combines random part and hash
        return f"{random_part}_{token_hash}"
    
    def validate_download_token(self, token: str) -> bool:
        """
        Validate download token format
        
        Args:
            token: Download token to validate
            
        Returns:
            True if token format is valid, False otherwise
        """
        # Basic format validation
        if not token or not isinstance(token, str):
            return False
        
        # Check token parts
        parts = token.split("_")
        if len(parts) != 2:
            return False
        
        # Check lengths
        if len(parts[0]) != 22 or len(parts[1]) != 32:  # Base64 URL-safe length and hash length
            return False
        
        return True
    
    async def get_file_stream(self, file_path: str) -> StreamingResponse:
        """
        Get a file as a streaming response
        
        Args:
            file_path: Path to the file
            
        Returns:
            StreamingResponse with the file content
        """
        # Check if path is relative or absolute
        if not os.path.isabs(file_path):
            full_path = os.path.join(self.storage_dir, file_path)
        else:
            full_path = file_path
        
        if not os.path.exists(full_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error_code": "FILE_NOT_FOUND", "message": "File not found"}
            )
        
        # Get file size and name for headers
        file_size = os.path.getsize(full_path)
        filename = os.path.basename(full_path)
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(full_path)
        if not content_type:
            content_type = "application/octet-stream"
        
        # Define async generator for streaming
        async def file_stream():
            async with aiofiles.open(full_path, "rb") as f:
                while chunk := await f.read(self.chunk_size):
                    yield chunk
        
        # Create streaming response
        response = StreamingResponse(file_stream(), media_type=content_type)
        
        # Add headers
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.headers["Content-Length"] = str(file_size)
        
        return response
    
    async def get_file_stream_range(self, file_path: str, start_byte: int = 0) -> StreamingResponse:
        """
        Get a file as a streaming response with range support
        
        Args:
            file_path: Path to the file
            start_byte: Starting byte for range request
            
        Returns:
            StreamingResponse with the file content from the specified range
        """
        # Check if path is relative or absolute
        if not os.path.isabs(file_path):
            full_path = os.path.join(self.storage_dir, file_path)
        else:
            full_path = file_path
        
        if not os.path.exists(full_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error_code": "FILE_NOT_FOUND", "message": "File not found"}
            )
        
        # Get file size and name for headers
        file_size = os.path.getsize(full_path)
        filename = os.path.basename(full_path)
        
        # Validate start_byte
        if start_byte < 0:
            start_byte = 0
        elif start_byte >= file_size:
            raise HTTPException(
                status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                detail={"error_code": "INVALID_RANGE", "message": "Requested range not satisfiable"}
            )
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(full_path)
        if not content_type:
            content_type = "application/octet-stream"
        
        # Define async generator for streaming with range
        async def file_stream_range():
            async with aiofiles.open(full_path, "rb") as f:
                # Seek to start position
                await f.seek(start_byte)
                
                # Stream from that position
                while chunk := await f.read(self.chunk_size):
                    yield chunk
        
        # Create streaming response
        response = StreamingResponse(
            file_stream_range(),
            media_type=content_type,
            status_code=status.HTTP_206_PARTIAL_CONTENT if start_byte > 0 else status.HTTP_200_OK
        )
        
        # Add headers
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.headers["Content-Length"] = str(file_size - start_byte)
        
        # Add range headers if this is a partial response
        if start_byte > 0:
            response.headers["Content-Range"] = f"bytes {start_byte}-{file_size-1}/{file_size}"
        
        return response
    
    async def get_file_response(self, file_path: str) -> FileResponse:
        """
        Get a file as a FileResponse (non-streaming)
        
        Args:
            file_path: Path to the file
            
        Returns:
            FileResponse with the file content
        """
        # Check if path is relative or absolute
        if not os.path.isabs(file_path):
            full_path = os.path.join(self.storage_dir, file_path)
        else:
            full_path = file_path
        
        if not os.path.exists(full_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error_code": "FILE_NOT_FOUND", "message": "File not found"}
            )
        
        # Get filename for headers
        filename = os.path.basename(full_path)
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(full_path)
        
        # Create file response
        return FileResponse(
            path=full_path,
            filename=filename,
            media_type=content_type
        )

# Create a singleton instance
storage_service = StorageService()