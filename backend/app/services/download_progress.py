"""
Download Progress Tracker Service for Enhanced Dataset Management
Tracks and reports download progress in real-time
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import time

from app.models.dataset import DatasetDownload

logger = logging.getLogger(__name__)


class DownloadProgressTracker:
    """Service for tracking download progress"""
    
    def __init__(self, db: Session):
        self.db = db
        self.active_downloads = {}  # In-memory tracking of active downloads
    
    def start_tracking(self, download_id: int, total_bytes: int) -> Dict[str, Any]:
        """
        Start tracking a download
        
        Args:
            download_id: Download record ID
            total_bytes: Total bytes to download
            
        Returns:
            Dict with tracking information
        """
        self.active_downloads[download_id] = {
            "download_id": download_id,
            "total_bytes": total_bytes,
            "bytes_transferred": 0,
            "start_time": time.time(),
            "last_update_time": time.time(),
            "transfer_rate_bps": 0,
            "percentage": 0,
            "estimated_time_remaining": None
        }
        
        return self.active_downloads[download_id]
    
    def update_progress(
        self,
        download_id: int,
        bytes_transferred: int,
        update_db: bool = True
    ) -> Dict[str, Any]:
        """
        Update download progress
        
        Args:
            download_id: Download record ID
            bytes_transferred: Bytes transferred so far
            update_db: Whether to update the database record
            
        Returns:
            Dict with updated tracking information
        """
        if download_id not in self.active_downloads:
            return {"error": "Download not being tracked"}
        
        tracking_info = self.active_downloads[download_id]
        
        # Update tracking information
        current_time = time.time()
        elapsed_time = current_time - tracking_info["last_update_time"]
        
        # Only update if some time has passed
        if elapsed_time > 0.1:  # Update every 100ms
            # Calculate transfer rate
            bytes_since_last_update = bytes_transferred - tracking_info["bytes_transferred"]
            transfer_rate_bps = bytes_since_last_update / elapsed_time
            
            # Update tracking info
            tracking_info["bytes_transferred"] = bytes_transferred
            tracking_info["last_update_time"] = current_time
            tracking_info["transfer_rate_bps"] = transfer_rate_bps
            
            # Calculate percentage
            if tracking_info["total_bytes"] > 0:
                tracking_info["percentage"] = int((bytes_transferred / tracking_info["total_bytes"]) * 100)
            
            # Calculate estimated time remaining
            if transfer_rate_bps > 0:
                bytes_remaining = tracking_info["total_bytes"] - bytes_transferred
                tracking_info["estimated_time_remaining"] = int(bytes_remaining / transfer_rate_bps)
            
            # Update database if requested
            if update_db:
                try:
                    download_record = self.db.query(DatasetDownload).filter(
                        DatasetDownload.id == download_id
                    ).first()
                    
                    if download_record:
                        download_record.progress_percentage = tracking_info["percentage"]
                        
                        # Calculate transfer rate in Mbps for display
                        mbps = (transfer_rate_bps * 8) / (1024 * 1024)  # Convert to megabits per second
                        download_record.transfer_rate_mbps = f"{mbps:.2f}"
                        
                        self.db.commit()
                except Exception as e:
                    logger.error(f"Failed to update download progress in database: {e}")
        
        return tracking_info
    
    def complete_tracking(self, download_id: int) -> Dict[str, Any]:
        """
        Complete download tracking
        
        Args:
            download_id: Download record ID
            
        Returns:
            Dict with final tracking information
        """
        if download_id not in self.active_downloads:
            return {"error": "Download not being tracked"}
        
        tracking_info = self.active_downloads[download_id]
        
        # Calculate final statistics
        total_time = time.time() - tracking_info["start_time"]
        average_rate_bps = tracking_info["total_bytes"] / total_time if total_time > 0 else 0
        
        # Update tracking info
        tracking_info["bytes_transferred"] = tracking_info["total_bytes"]
        tracking_info["percentage"] = 100
        tracking_info["transfer_rate_bps"] = average_rate_bps
        tracking_info["estimated_time_remaining"] = 0
        tracking_info["completed"] = True
        tracking_info["total_time_seconds"] = total_time
        
        # Update database
        try:
            download_record = self.db.query(DatasetDownload).filter(
                DatasetDownload.id == download_id
            ).first()
            
            if download_record:
                download_record.progress_percentage = 100
                download_record.download_status = "completed"
                download_record.completed_at = datetime.utcnow()
                download_record.download_duration_seconds = int(total_time)
                
                # Calculate transfer rate in Mbps for display
                mbps = (average_rate_bps * 8) / (1024 * 1024)  # Convert to megabits per second
                download_record.transfer_rate_mbps = f"{mbps:.2f}"
                
                self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update download completion in database: {e}")
        
        # Remove from active downloads after a delay
        def cleanup_later():
            import threading
            def remove_after_delay():
                time.sleep(60)  # Keep tracking info for 1 minute after completion
                if download_id in self.active_downloads:
                    del self.active_downloads[download_id]
            
            thread = threading.Thread(target=remove_after_delay)
            thread.daemon = True
            thread.start()
        
        cleanup_later()
        
        return tracking_info
    
    def get_progress(self, download_id: int) -> Dict[str, Any]:
        """
        Get current progress for a download
        
        Args:
            download_id: Download record ID
            
        Returns:
            Dict with current tracking information
        """
        # Check in-memory tracking first
        if download_id in self.active_downloads:
            return self.active_downloads[download_id]
        
        # If not in memory, check database
        try:
            download_record = self.db.query(DatasetDownload).filter(
                DatasetDownload.id == download_id
            ).first()
            
            if download_record:
                return {
                    "download_id": download_record.id,
                    "percentage": download_record.progress_percentage or 0,
                    "status": download_record.download_status,
                    "transfer_rate_mbps": download_record.transfer_rate_mbps,
                    "from_database": True
                }
        except Exception as e:
            logger.error(f"Failed to get download progress from database: {e}")
        
        return {"error": "Download not found"}