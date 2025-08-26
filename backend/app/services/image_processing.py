"""
Image Processing Service for AI Share Platform
Handles image processing tasks for file uploads and analysis
"""

import logging
from typing import Optional, Dict, Any, List
from PIL import Image
import io
import base64

logger = logging.getLogger(__name__)


class ImageProcessingService:
    """Service for handling image processing tasks"""
    
    def __init__(self):
        self.supported_formats = ['JPEG', 'PNG', 'GIF', 'BMP', 'WEBP']
        self.max_size = (1920, 1080)  # Max dimensions
    
    def process_image(self, image_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Process uploaded image data
        
        Args:
            image_data: Raw image bytes
            filename: Original filename
            
        Returns:
            Dict containing processed image information
        """
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Get basic info
            info = {
                'filename': filename,
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.width,
                'height': image.height
            }
            
            # Resize if too large
            if image.width > self.max_size[0] or image.height > self.max_size[1]:
                image.thumbnail(self.max_size, Image.Resampling.LANCZOS)
                info['resized'] = True
                info['new_size'] = image.size
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = rgb_image
                info['converted_to_rgb'] = True
            
            # Save processed image to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85)
            processed_data = output.getvalue()
            
            info['processed_size'] = len(processed_data)
            info['processed_data'] = processed_data
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to process image {filename}: {e}")
            raise
    
    def get_image_preview(self, image_data: bytes, max_size: tuple = (400, 300)) -> str:
        """
        Generate a base64 preview of an image
        
        Args:
            image_data: Raw image bytes
            max_size: Maximum dimensions for preview
            
        Returns:
            Base64 encoded preview image
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Create thumbnail
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = rgb_image
            
            # Save to base64
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=70)
            preview_data = output.getvalue()
            
            return base64.b64encode(preview_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to generate image preview: {e}")
            return ""
    
    def is_supported_format(self, filename: str) -> bool:
        """Check if image format is supported"""
        try:
            # Try to determine format from filename
            ext = filename.lower().split('.')[-1] if '.' in filename else ''
            supported_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
            return ext in supported_extensions
        except:
            return False
    
    def get_image_metadata(self, image_data: bytes) -> Dict[str, Any]:
        """Extract metadata from image"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            metadata = {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.width,
                'height': image.height,
                'has_transparency': image.mode in ('RGBA', 'LA') or 'transparency' in image.info
            }
            
            # Extract EXIF data if available
            if hasattr(image, '_getexif') and image._getexif():
                metadata['exif'] = dict(image._getexif())
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to extract image metadata: {e}")
            return {}