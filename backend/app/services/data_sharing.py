from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.user import User
from app.models.dataset import Dataset, DatasetAccessLog
from app.models.organization import Organization, Department, DataSharingLevel, UserRole
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataSharingService:
    """Service for managing organization-scoped data sharing and access control"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def can_access_dataset(self, user: User, dataset: Dataset) -> bool:
        """
        Check if a user can access a dataset within their organization.
        All data sharing is organization-scoped only.
        """
        # Users can only access datasets from their own organization
        if not user.organization_id or user.organization_id != dataset.organization_id:
            return False
        
        # Owner can always access their own datasets
        if dataset.owner_id == user.id:
            return True
        
        # Check sharing level within the organization
        if dataset.sharing_level == DataSharingLevel.PRIVATE:
            return False
        
        elif dataset.sharing_level == DataSharingLevel.ORGANIZATION:
            # All organization members can access
            return True
        
        elif dataset.sharing_level == DataSharingLevel.DEPARTMENT:
            # Only department members can access
            return (user.department_id and 
                   user.department_id == dataset.department_id)
        
        return False
    
    def get_accessible_datasets(self, user: User, 
                              sharing_level: Optional[DataSharingLevel] = None) -> List[Dataset]:
        """
        Get all datasets accessible to a user within their organization.
        """
        if not user.organization_id:
            return []
        
        query = self.db.query(Dataset).filter(
            Dataset.organization_id == user.organization_id
        )
        
        # Filter by sharing level if specified
        if sharing_level:
            query = query.filter(Dataset.sharing_level == sharing_level)
        
        datasets = query.all()
        
        # Filter based on access permissions
        accessible_datasets = []
        for dataset in datasets:
            if self.can_access_dataset(user, dataset):
                accessible_datasets.append(dataset)
        
        return accessible_datasets
    
    def get_organization_datasets(self, organization_id: int, 
                                user: User) -> List[Dataset]:
        """
        Get all datasets for an organization (admin/manager view).
        Only organization admins/owners can see all datasets.
        """
        if (not user.organization_id or 
            user.organization_id != organization_id or
            user.role not in ["owner", "admin"]):
            return []
        
        return self.db.query(Dataset).filter(
            Dataset.organization_id == organization_id
        ).all()
    
    def log_access(self, user: User, dataset: Dataset, access_type: str,
                   ip_address: Optional[str] = None, 
                   user_agent: Optional[str] = None) -> bool:
        """Log dataset access for audit purposes"""
        if not self.can_access_dataset(user, dataset):
            return False
        
        access_log = DatasetAccessLog(
            dataset_id=dataset.id,
            user_id=user.id,
            access_type=access_type,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(access_log)
        self.db.commit()
        
        # Update last accessed timestamp
        dataset.last_accessed = access_log.created_at
        self.db.commit()
        
        return True
    
    def get_organization_stats(self, organization_id: int, user: User) -> dict:
        """
        Get organization data usage statistics.
        Only available to organization admins/owners.
        """
        if (not user.organization_id or 
            user.organization_id != organization_id or
            user.role not in ["owner", "admin"]):
            return {}
        
        datasets = self.db.query(Dataset).filter(
            Dataset.organization_id == organization_id
        ).all()
        
        total_datasets = len(datasets)
        
        # Count by sharing level
        sharing_stats = {
            DataSharingLevel.ORGANIZATION: 0,
            DataSharingLevel.DEPARTMENT: 0,
            DataSharingLevel.PRIVATE: 0
        }
        
        total_size = 0
        for dataset in datasets:
            sharing_stats[dataset.sharing_level] += 1
            if dataset.size_bytes:
                total_size += dataset.size_bytes
        
        # Recent access count
        recent_accesses = self.db.query(DatasetAccessLog).join(Dataset).filter(
            Dataset.organization_id == organization_id
        ).count()
        
        return {
            "total_datasets": total_datasets,
            "total_size_bytes": total_size,
            "sharing_levels": sharing_stats,
            "recent_accesses": recent_accesses,
            "organization_id": organization_id
        }
    
    def check_department_access(self, user: User, department_id: int) -> bool:
        """Check if user can access department-level data"""
        return (user.department_id == department_id and 
               user.organization_id is not None)
    
    def validate_dataset_creation(self, user: User, organization_id: int) -> bool:
        """
        Validate if user can create dataset in the organization.
        Users can only create datasets in their own organization.
        """
        return (user.organization_id == organization_id and
               user.role in ["owner", "admin", "manager", "member"])
    
    def update_sharing_level(self, user: User, dataset: Dataset, 
                           new_sharing_level: DataSharingLevel) -> bool:
        """
        Update dataset sharing level within organization.
        Only owner and admins can change sharing levels.
        """
        # Check permissions
        if not (dataset.owner_id == user.id or 
               (user.organization_id == dataset.organization_id and 
                user.role in ["owner", "admin"])):
            return False
        
        dataset.sharing_level = new_sharing_level
        self.db.commit()
        
        logger.info(f"Dataset {dataset.id} sharing level updated to {new_sharing_level} by user {user.id}")
        return True
    
    def get_sharing_stats(self, organization_id: int, user: User) -> dict:
        """
        Get data sharing statistics for an organization (organization-scoped only)
        """
        if (not user.organization_id or 
            user.organization_id != organization_id or
            user.role not in ["owner", "admin"]):
            return {}
        
        # Get datasets by sharing level
        datasets = self.db.query(Dataset).filter(
            Dataset.organization_id == organization_id
        ).all()
        
        stats = {
            "total_datasets": len(datasets),
            "by_sharing_level": {
                "private": 0,
                "department": 0,
                "organization": 0
            },
            "by_type": {},
            "total_access_logs": 0,
            "unique_users_accessed": 0
        }
        
        # Count by sharing level (no public level)
        for dataset in datasets:
            level = dataset.sharing_level.value if dataset.sharing_level else "private"
            if level in stats["by_sharing_level"]:
                stats["by_sharing_level"][level] += 1
            
            # Count by type
            dataset_type = dataset.type.value if dataset.type else "unknown"
            stats["by_type"][dataset_type] = stats["by_type"].get(dataset_type, 0) + 1
        
        # Get access statistics
        access_logs = self.db.query(DatasetAccessLog).join(Dataset).filter(
            Dataset.organization_id == organization_id
        ).all()
        
        stats["total_access_logs"] = len(access_logs)
        stats["unique_users_accessed"] = len(set(log.user_id for log in access_logs))
        
        return stats
    
    def get_department_datasets(
        self, 
        department_id: int, 
        user: User
    ) -> List[Dataset]:
        """
        Get datasets shared within a specific department
        """
        # Check if user has access to this department
        if (not user.organization_id or 
            user.department_id != department_id and
            user.role not in ["owner", "admin"]):
            return []
        
        return self.db.query(Dataset).filter(
            Dataset.department_id == department_id,
            Dataset.sharing_level == DataSharingLevel.DEPARTMENT
        ).all()
    
    def get_organization_shared_datasets(
        self, 
        organization_id: int, 
        user: User
    ) -> List[Dataset]:
        """
        Get all datasets shared at organization level (organization-scoped only)
        """
        # Check if user has access to this organization
        if (not user.organization_id or 
            user.organization_id != organization_id):
            return []
        
        return self.db.query(Dataset).filter(
            Dataset.organization_id == organization_id,
            Dataset.sharing_level == DataSharingLevel.ORGANIZATION
        ).all() 