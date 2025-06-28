from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
from enum import Enum

from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.dataset import Dataset
from app.models.analytics import ActivityLog
from app.core.auth import get_current_user

router = APIRouter()

# Enums for request types and statuses
class RequestType(str, Enum):
    ACCESS = "access"
    DOWNLOAD = "download"
    SHARE = "share"

class AccessLevel(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class RequestCategory(str, Enum):
    RESEARCH = "research"
    ANALYSIS = "analysis"
    COMPLIANCE = "compliance"
    REPORTING = "reporting"
    DEVELOPMENT = "development"

# Request Models
class AccessRequestCreate(BaseModel):
    dataset_id: int
    request_type: RequestType
    requested_level: AccessLevel
    purpose: str
    justification: str
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM
    category: RequestCategory = RequestCategory.ANALYSIS
    expiry_date: Optional[str] = None

class AccessRequestResponse(BaseModel):
    id: int
    requester_id: int
    requester_name: str
    requester_email: str
    requester_department: str
    dataset_id: int
    dataset_name: str
    dataset_owner: str
    request_type: RequestType
    requested_level: AccessLevel
    purpose: str
    justification: str
    request_date: str
    expiry_date: Optional[str] = None
    status: RequestStatus
    approved_by: Optional[str] = None
    approved_date: Optional[str] = None
    rejection_reason: Optional[str] = None
    urgency: UrgencyLevel
    category: RequestCategory

class DatasetAccessResponse(BaseModel):
    id: int
    name: str
    description: str
    owner: str
    owner_department: str
    sharing_level: str
    size: float
    last_updated: str
    access_count: int
    has_access: bool
    can_request: bool
    tags: List[str]

class AccessRequestApproval(BaseModel):
    decision: str  # "approve" or "reject"
    reason: Optional[str] = None
    expiry_date: Optional[str] = None

class AuditLogResponse(BaseModel):
    id: int
    action: str
    user_id: int
    user_name: str
    dataset_id: int
    dataset_name: str
    timestamp: str
    details: str
    ip_address: str
    user_agent: str

# Mock data storage (replace with actual database models)
access_requests_storage = []
audit_logs_storage = []

@router.get("/datasets", response_model=List[DatasetAccessResponse])
async def get_accessible_datasets(
    search: Optional[str] = Query(None, description="Search term"),
    sharing_level: Optional[str] = Query(None, description="Filter by sharing level"),
    department: Optional[str] = Query(None, description="Filter by department"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all datasets that user can see or request access to
    """
    if not current_user.organization_id:
        # Return empty list for users without organizations
        return []
    
    # Get datasets from user's organization
    query = db.query(Dataset).filter(
        Dataset.organization_id == current_user.organization_id
    )
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                Dataset.name.contains(search),
                Dataset.description.contains(search)
            )
        )
    
    if sharing_level and sharing_level != "all":
        query = query.filter(Dataset.sharing_level == sharing_level)
    
    datasets = query.all()
    
    result = []
    for dataset in datasets:
        # Determine access status
        has_access = dataset.owner_id == current_user.id or dataset.sharing_level in ["ORGANIZATION", "DEPARTMENT"]
        can_request = not has_access and dataset.sharing_level == "PRIVATE"
        
        result.append(DatasetAccessResponse(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            owner=dataset.owner.full_name if dataset.owner and dataset.owner.full_name else (dataset.owner.email.split('@')[0] if dataset.owner else "Unknown"),
            owner_department="Analytics",  # Mock data
            sharing_level=dataset.sharing_level,
            size=round(dataset.size_bytes / (1024**3), 2) if dataset.size_bytes else 0.0,
            last_updated=dataset.updated_at.isoformat() if dataset.updated_at else datetime.now().isoformat(),
            access_count=max(10, dataset.id * 12),  # Mock access count
            has_access=has_access,
            can_request=can_request,
            tags=["data", "analytics", "2024"]  # Mock tags
        ))
    
    return result

@router.post("/requests", response_model=Dict[str, str])
async def create_access_request(
    request_data: AccessRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new access request for a dataset
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization to create access requests")
    
    # Get the dataset
    dataset = db.query(Dataset).filter(
        Dataset.id == request_data.dataset_id,
        Dataset.organization_id == current_user.organization_id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Check if user already has access
    if dataset.owner_id == current_user.id or dataset.sharing_level in ["ORGANIZATION", "DEPARTMENT"]:
        raise HTTPException(status_code=400, detail="User already has access to this dataset")
    
    # Create access request (mock storage)
    new_request = {
        "id": len(access_requests_storage) + 1,
        "requester_id": current_user.id,
        "requester_name": current_user.full_name or current_user.email.split('@')[0],
        "requester_email": current_user.email,
        "requester_department": "Current Department",  # Mock department
        "dataset_id": dataset.id,
        "dataset_name": dataset.name,
        "dataset_owner": "Dataset Owner",  # Mock owner
        "request_type": request_data.request_type,
        "requested_level": request_data.requested_level,
        "purpose": request_data.purpose,
        "justification": request_data.justification,
        "request_date": datetime.now().isoformat(),
        "expiry_date": request_data.expiry_date,
        "status": RequestStatus.PENDING,
        "urgency": request_data.urgency,
        "category": request_data.category
    }
    
    access_requests_storage.append(new_request)
    
    # Log the activity
    await log_audit_activity(
        action="ACCESS_REQUESTED",
        user_id=current_user.id,
        user_name=current_user.full_name or current_user.email,
        dataset_id=dataset.id,
        dataset_name=dataset.name,
        details=f"Access request submitted for {request_data.request_type} access",
        ip_address="192.168.1.1",  # Mock IP
        user_agent="MockAgent"
    )
    
    return {"message": "Access request submitted successfully", "request_id": str(new_request["id"])}

@router.get("/requests", response_model=List[AccessRequestResponse])
async def get_access_requests(
    status: Optional[RequestStatus] = Query(None, description="Filter by status"),
    urgency: Optional[UrgencyLevel] = Query(None, description="Filter by urgency"),
    my_requests: bool = Query(False, description="Show only current user's requests"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get access requests (all for admins, user's own requests for regular users)
    """
    if not current_user.organization_id:
        # Return empty list for users without organizations
        return []
    
    # Filter requests
    filtered_requests = access_requests_storage.copy()
    
    if my_requests or not current_user.is_superuser:
        filtered_requests = [r for r in filtered_requests if r["requester_id"] == current_user.id]
    
    if status:
        filtered_requests = [r for r in filtered_requests if r["status"] == status]
    
    if urgency:
        filtered_requests = [r for r in filtered_requests if r["urgency"] == urgency]
    
    # Convert to response model
    result = []
    for request in filtered_requests:
        result.append(AccessRequestResponse(**request))
    
    return result

@router.put("/requests/{request_id}/approve")
async def approve_access_request(
    request_id: int,
    approval_data: AccessRequestApproval,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve or reject an access request
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization to approve requests")
    
    # Find the request
    request = None
    for req in access_requests_storage:
        if req["id"] == request_id:
            request = req
            break
    
    if not request:
        raise HTTPException(status_code=404, detail="Access request not found")
    
    if request["status"] != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request is not pending")
    
    # Update request status
    if approval_data.decision == "approve":
        request["status"] = RequestStatus.APPROVED
        request["approved_by"] = current_user.full_name or current_user.email
        request["approved_date"] = datetime.now().isoformat()
        if approval_data.expiry_date:
            request["expiry_date"] = approval_data.expiry_date
        
        action = "ACCESS_GRANTED"
        details = "Access request approved"
    else:
        request["status"] = RequestStatus.REJECTED
        request["rejection_reason"] = approval_data.reason or "No reason provided"
        
        action = "ACCESS_DENIED"
        details = f"Access request rejected: {approval_data.reason or 'No reason provided'}"
    
    # Log the activity
    await log_audit_activity(
        action=action,
        user_id=current_user.id,
        user_name=current_user.full_name or current_user.email,
        dataset_id=request["dataset_id"],
        dataset_name=request["dataset_name"],
        details=details,
        ip_address="192.168.1.1",  # Mock IP
        user_agent="MockAgent"
    )
    
    return {"message": f"Request {approval_data.decision}d successfully"}

@router.get("/audit", response_model=List[AuditLogResponse])
async def get_audit_trail(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    action: Optional[str] = Query(None, description="Filter by action"),
    dataset_id: Optional[int] = Query(None, description="Filter by dataset"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get audit trail for data access activities
    """
    if not current_user.organization_id:
        # Return empty list for users without organizations
        return []
    
    # Filter audit logs
    filtered_logs = audit_logs_storage.copy()
    
    if action:
        filtered_logs = [log for log in filtered_logs if action.upper() in log["action"]]
    
    if dataset_id:
        filtered_logs = [log for log in filtered_logs if log["dataset_id"] == dataset_id]
    
    # Apply date filters if provided
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        filtered_logs = [
            log for log in filtered_logs 
            if datetime.fromisoformat(log["timestamp"]) >= start_dt
        ]
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        filtered_logs = [
            log for log in filtered_logs 
            if datetime.fromisoformat(log["timestamp"]) < end_dt
        ]
    
    # Sort by timestamp (newest first)
    filtered_logs.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Convert to response model
    result = []
    for log in filtered_logs:
        result.append(AuditLogResponse(**log))
    
    return result

@router.post("/notify")
async def send_notification(
    recipient_email: str,
    subject: str,
    message: str,
    notification_type: str = "access_request",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send notification for access request events
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    # Mock notification sending
    notification_data = {
        "recipient": recipient_email,
        "subject": subject,
        "message": message,
        "type": notification_type,
        "sent_at": datetime.now().isoformat(),
        "sent_by": current_user.email
    }
    
    # In a real implementation, this would integrate with email service
    # For now, just log the notification
    await log_audit_activity(
        action="NOTIFICATION_SENT",
        user_id=current_user.id,
        user_name=current_user.full_name or current_user.email,
        dataset_id=0,  # Not dataset-specific
        dataset_name="System",
        details=f"Notification sent to {recipient_email}: {subject}",
        ip_address="192.168.1.1",
        user_agent="MockAgent"
    )
    
    return {"message": "Notification sent successfully", "notification": notification_data}

@router.get("/requests/{request_id}")
async def get_access_request_details(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific access request
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    # Find the request
    request = None
    for req in access_requests_storage:
        if req["id"] == request_id:
            request = req
            break
    
    if not request:
        raise HTTPException(status_code=404, detail="Access request not found")
    
    # Check permissions (users can only see their own requests unless they're admin)
    if not current_user.is_superuser and request["requester_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this request")
    
    return AccessRequestResponse(**request)

@router.delete("/requests/{request_id}")
async def cancel_access_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a pending access request
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    # Find the request
    request_index = None
    request = None
    for i, req in enumerate(access_requests_storage):
        if req["id"] == request_id:
            request_index = i
            request = req
            break
    
    if not request:
        raise HTTPException(status_code=404, detail="Access request not found")
    
    # Check permissions (users can only cancel their own requests)
    if request["requester_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this request")
    
    if request["status"] != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only cancel pending requests")
    
    # Remove the request
    access_requests_storage.pop(request_index)
    
    # Log the activity
    await log_audit_activity(
        action="REQUEST_CANCELLED",
        user_id=current_user.id,
        user_name=current_user.full_name or current_user.email,
        dataset_id=request["dataset_id"],
        dataset_name=request["dataset_name"],
        details="Access request cancelled by requester",
        ip_address="192.168.1.1",
        user_agent="MockAgent"
    )
    
    return {"message": "Access request cancelled successfully"}

async def log_audit_activity(
    action: str,
    user_id: int,
    user_name: str,
    dataset_id: int,
    dataset_name: str,
    details: str,
    ip_address: str,
    user_agent: str
):
    """
    Log an audit activity
    """
    audit_entry = {
        "id": len(audit_logs_storage) + 1,
        "action": action,
        "user_id": user_id,
        "user_name": user_name,
        "dataset_id": dataset_id,
        "dataset_name": dataset_name,
        "timestamp": datetime.now().isoformat(),
        "details": details,
        "ip_address": ip_address,
        "user_agent": user_agent
    }
    
    audit_logs_storage.append(audit_entry)

# Initialize with some sample data
def initialize_sample_data():
    """Initialize sample access requests and audit logs"""
    
    # Sample access requests
    sample_requests = [
        {
            "id": 1,
            "requester_id": 1,
            "requester_name": "John Smith",
            "requester_email": "john.smith@techcorp.com",
            "requester_department": "Sales",
            "dataset_id": 1,
            "dataset_name": "Financial_Reports_Confidential_2023",
            "dataset_owner": "Michael Chen",
            "request_type": RequestType.ACCESS,
            "requested_level": AccessLevel.READ,
            "purpose": "Quarterly sales analysis and revenue forecasting",
            "justification": "Need access to financial data to create accurate sales projections for Q1 2024.",
            "request_date": "2024-01-15T10:30:00Z",
            "expiry_date": "2024-03-15T10:30:00Z",
            "status": RequestStatus.PENDING,
            "urgency": UrgencyLevel.HIGH,
            "category": RequestCategory.ANALYSIS
        },
        {
            "id": 2,
            "requester_id": 2,
            "requester_name": "Lisa Wong",
            "requester_email": "lisa.wong@techcorp.com",
            "requester_department": "Research",
            "dataset_id": 2,
            "dataset_name": "Product_Development_Research_Internal",
            "dataset_owner": "David Kim",
            "request_type": RequestType.DOWNLOAD,
            "requested_level": AccessLevel.READ,
            "purpose": "Competitive analysis research project",
            "justification": "Conducting market research study that requires analysis of product development patterns.",
            "request_date": "2024-01-14T14:15:00Z",
            "status": RequestStatus.APPROVED,
            "approved_by": "David Kim",
            "approved_date": "2024-01-15T09:20:00Z",
            "urgency": UrgencyLevel.MEDIUM,
            "category": RequestCategory.RESEARCH
        }
    ]
    
    # Sample audit logs
    sample_audit_logs = [
        {
            "id": 1,
            "action": "ACCESS_GRANTED",
            "user_id": 2,
            "user_name": "Lisa Wong",
            "dataset_id": 2,
            "dataset_name": "Product_Development_Research_Internal",
            "timestamp": "2024-01-15T09:20:00Z",
            "details": "Access granted by David Kim for research project",
            "ip_address": "192.168.1.45",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        {
            "id": 2,
            "action": "DATA_DOWNLOADED",
            "user_id": 2,
            "user_name": "Lisa Wong",
            "dataset_id": 2,
            "dataset_name": "Product_Development_Research_Internal",
            "timestamp": "2024-01-15T10:15:00Z",
            "details": "Dataset downloaded following approved access request",
            "ip_address": "192.168.1.45",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        {
            "id": 3,
            "action": "ACCESS_DENIED",
            "user_id": 3,
            "user_name": "Robert Taylor",
            "dataset_id": 1,
            "dataset_name": "Financial_Reports_Confidential_2023",
            "timestamp": "2024-01-12T17:30:00Z",
            "details": "Access request rejected due to insufficient clearance",
            "ip_address": "192.168.1.78",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    ]
    
    access_requests_storage.extend(sample_requests)
    audit_logs_storage.extend(sample_audit_logs)

# Initialize sample data when module loads
initialize_sample_data() 