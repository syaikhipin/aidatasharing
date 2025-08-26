"""
File Server API for serving stored files to external services like MindsDB
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.services.storage import storage_service
import logging
from urllib.parse import unquote

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/serve/{file_path:path}")
async def serve_file(file_path: str):
    """
    Serve a file from storage for external access (MindsDB, etc.)
    This endpoint provides direct file access for AI/ML services
    """
    try:
        # Decode the file path
        decoded_path = unquote(file_path)
        
        logger.info(f"Serving file: {decoded_path}")
        
        # Get file stream from storage service
        response = await storage_service.get_dataset_file_stream(decoded_path)
        
        # Add CORS headers for external access
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET"
        response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error serving file {file_path}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error serving file: {str(e)}"
        )


@router.get("/url/{file_path:path}")
async def get_file_url(file_path: str, expires_in: int = 3600):
    """
    Get a direct URL to access a file (useful for S3 presigned URLs)
    """
    try:
        # Decode the file path
        decoded_path = unquote(file_path)
        
        logger.info(f"Getting URL for file: {decoded_path}")
        
        # Get file URL from storage service
        url = storage_service.get_dataset_file_url(decoded_path, expires_in)
        
        if not url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found or URL generation failed"
            )
        
        return {
            "file_path": decoded_path,
            "url": url,
            "expires_in": expires_in
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error getting URL for file {file_path}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting file URL: {str(e)}"
        )