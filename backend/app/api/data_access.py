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
from app.models.analytics import ActivityLog, AccessRequest, AuditLog, RequestType, AccessLevel, RequestStatus, UrgencyLevel, RequestCategory, Notification
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
class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: str
    sender_name: Optional[str] = None
    related_resource_type: Optional[str] = None
    related_resource_id: Optional[int] = None

# Mock data storage (replace with actual database models)
# access_requests_storage = []
# audit_logs_storage = []

@router.get("/datasets", response_model=List[DatasetAccessResponse])
async def get_accessible_datasets(
    search: Optional[str] = Query(None, description="Search term"),
    sharing_level: Optional[str] = Query(None, description="Filter by sharing level"),
    department: Optional[str] = Query(None, description="Filter by department"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all datasets that user can see or request access to from other users
    """
    if not current_user.organization_id:
        # Return empty list for users without organizations
        return []
    
    # Get datasets that are NOT owned by current user and NOT deleted
    query = db.query(Dataset).filter(
        Dataset.owner_id != current_user.id,  # Not owned by current user
        Dataset.is_deleted == False  # Not deleted
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
        # Determine access status based on sharing level and organization
        has_access = False
        can_request = False
        
        sharing_level_str = dataset.sharing_level.value if hasattr(dataset.sharing_level, 'value') else str(dataset.sharing_level)
        sharing_level_str = sharing_level_str.upper()  # Normalize to uppercase
        
        if sharing_level_str == "PUBLIC":
            has_access = True
        elif sharing_level_str == "ORGANIZATION" and dataset.organization_id == current_user.organization_id:
            has_access = True
        elif sharing_level_str == "PRIVATE":
            can_request = True
        
        # Only include datasets that user can either access or request access to
        if has_access or can_request:
            result.append(DatasetAccessResponse(
                id=dataset.id,
                name=dataset.name,
                description=dataset.description or "No description available",
                owner=dataset.owner.full_name if dataset.owner and dataset.owner.full_name else (dataset.owner.email.split('@')[0] if dataset.owner else "Unknown"),
                owner_department="Analytics",  # Mock data
                sharing_level=sharing_level_str,
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
    
    # Get the dataset (allow cross-organization access for sharing)
    dataset = db.query(Dataset).filter(
        Dataset.id == request_data.dataset_id,
        Dataset.is_deleted == False  # Only allow requests for non-deleted datasets
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found or has been deleted")
    
    # Check if user already has access
    if dataset.owner_id == current_user.id or dataset.sharing_level in ["ORGANIZATION", "DEPARTMENT"]:
        raise HTTPException(status_code=400, detail="User already has access to this dataset")
    
    # Create access request
    new_request = AccessRequest(
        requester_id=current_user.id,
        dataset_id=dataset.id,
        request_type=request_data.request_type,
        requested_level=request_data.requested_level,
        purpose=request_data.purpose,
        justification=request_data.justification,
        urgency=request_data.urgency,
        category=request_data.category,
        expiry_date=datetime.fromisoformat(request_data.expiry_date) if request_data.expiry_date else None,
        status=RequestStatus.PENDING
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    
    # Create notification for dataset owner
    notification = Notification(
        recipient_id=dataset.owner_id,
        sender_id=current_user.id,
        title=f"New Data Access Request for {dataset.name}",
        message=f"{current_user.full_name or current_user.email} has requested {request_data.requested_level} access to your dataset '{dataset.name}'. Purpose: {request_data.purpose}",
        notification_type="info",
        related_resource_type="access_request",
        related_resource_id=new_request.id
    )
    db.add(notification)
    db.commit()
    
    # Log the activity
    log_audit_activity(
        db=db,
        action="ACCESS_REQUESTED",
        user_id=current_user.id,
        dataset_id=dataset.id,
        details=f"Access request submitted for {request_data.request_type} access",
        ip_address="192.168.1.1",  # Mock IP, replace with real in production
        user_agent="MockAgent"  # Replace with real
    )
    
    return {"message": "Access request submitted successfully", "request_id": str(new_request.id)}

@router.get("/requests", response_model=List[AccessRequestResponse])
async def get_access_requests(
    status: Optional[RequestStatus] = Query(None, description="Filter by status"),
    urgency: Optional[UrgencyLevel] = Query(None, description="Filter by urgency"),
    my_requests: bool = Query(False, description="Show only current user's requests"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get access requests (dataset owners see requests for their datasets, requesters see their own requests)
    """
    if not current_user.organization_id:
        return []
    
    # Base query - requests within user's organization
    base_query = db.query(AccessRequest).filter(
        AccessRequest.dataset.has(organization_id=current_user.organization_id)
    )
    
    if my_requests:
        # User explicitly wants to see only their own requests
        query = base_query.filter(AccessRequest.requester_id == current_user.id)
    elif current_user.is_superuser:
        # Superusers see all requests in their organization
        query = base_query
    else:
        # Regular users see:
        # 1. Requests for datasets they own (so they can approve them)
        # 2. Requests they made themselves
        query = base_query.filter(
            or_(
                AccessRequest.dataset.has(owner_id=current_user.id),  # Requests for their datasets
                AccessRequest.requester_id == current_user.id         # Their own requests
            )
        )
    
    if status:
        query = query.filter(AccessRequest.status == status)
    
    if urgency:
        query = query.filter(AccessRequest.urgency == urgency)
    
    requests = query.all()
    
    result = []
    for req in requests:
        result.append(AccessRequestResponse(
            id=req.id,
            requester_id=req.requester_id,
            requester_name=req.requester.full_name or req.requester.email.split('@')[0],
            requester_email=req.requester.email,
            requester_department=req.requester.role or "Not specified",
            dataset_id=req.dataset_id,
            dataset_name=req.dataset.name,
            dataset_owner=req.dataset.owner.full_name or req.dataset.owner.email.split('@')[0],
            request_type=req.request_type,
            requested_level=req.requested_level,
            purpose=req.purpose,
            justification=req.justification,
            request_date=req.created_at.isoformat(),
            expiry_date=req.expiry_date.isoformat() if req.expiry_date else None,
            status=req.status,
            approved_by=req.approved_by.full_name if req.approved_by else None,
            approved_date=req.approved_date.isoformat() if req.approved_date else None,
            rejection_reason=req.rejection_reason,
            urgency=req.urgency,
            category=req.category
        ))
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
    
    request = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Access request not found")
    
    if request.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request is not pending")
    
    # Load the dataset to check ownership
    dataset = request.dataset
    if not dataset:
        raise HTTPException(status_code=404, detail="Associated dataset not found")
    
    # Check if current user is authorized to approve this request
    # Only dataset owner or superuser can approve
    if dataset.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403, 
            detail="Only the dataset owner can approve access requests"
        )
    
    if approval_data.decision == "approve":
        request.status = RequestStatus.APPROVED
        request.approved_by_id = current_user.id
        request.approved_date = datetime.utcnow()
        if approval_data.expiry_date:
            request.expiry_date = datetime.fromisoformat(approval_data.expiry_date)
        
        action = "ACCESS_GRANTED"
        details = "Access request approved"
        
        # Create notification for requester
        notification = Notification(
            recipient_id=request.requester_id,
            sender_id=current_user.id,
            title=f"Data Access Request Approved",
            message=f"Your request for {request.requested_level} access to '{request.dataset.name}' has been approved.",
            notification_type="success",
            related_resource_type="access_request",
            related_resource_id=request.id
        )
    else:
        request.status = RequestStatus.REJECTED
        request.rejection_reason = approval_data.reason or "No reason provided"
        
        action = "ACCESS_DENIED"
        details = f"Access request rejected: {approval_data.reason or 'No reason provided'}"
        
        # Create notification for requester
        notification = Notification(
            recipient_id=request.requester_id,
            sender_id=current_user.id,
            title=f"Data Access Request Rejected",
            message=f"Your request for {request.requested_level} access to '{request.dataset.name}' has been rejected. Reason: {approval_data.reason or 'No reason provided'}",
            notification_type="warning",
            related_resource_type="access_request",
            related_resource_id=request.id
        )
    
    db.add(notification)
    db.commit()
    
    # Log the activity
    log_audit_activity(
        db=db,
        action=action,
        user_id=current_user.id,
        dataset_id=request.dataset_id,
        details=details,
        ip_address="192.168.1.1",
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
        return []
    
    query = db.query(AuditLog).filter(
        AuditLog.dataset.has(organization_id=current_user.organization_id)
    )
    
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    
    if dataset_id:
        query = query.filter(AuditLog.dataset_id == dataset_id)
    
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(AuditLog.timestamp >= start_dt)
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(AuditLog.timestamp < end_dt)
    
    query = query.order_by(desc(AuditLog.timestamp))
    
    logs = query.all()
    
    result = []
    for log in logs:
        result.append(AuditLogResponse(
            id=log.id,
            action=log.action,
            user_id=log.user_id,
            user_name=log.user.full_name or log.user.email,
            dataset_id=log.dataset_id,
            dataset_name=log.dataset.name,
            timestamp=log.timestamp.isoformat(),
            details=log.details,
            ip_address=log.ip_address,
            user_agent=log.user_agent
        ))
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
    log_audit_activity(
        db=db,
        action="NOTIFICATION_SENT",
        user_id=current_user.id,
        dataset_id=0,  # Not dataset-specific
        details=f"Notification sent to {recipient_email}: {subject}",
        ip_address="192.168.1.1",
        user_agent="MockAgent"
    )
    
    return {"message": "Notification sent successfully", "notification": notification_data}

@router.get("/requests/{request_id}", response_model=AccessRequestResponse)
async def get_request_details(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific access request
    """
    request = db.query(AccessRequest).filter(
        AccessRequest.id == request_id,
        AccessRequest.dataset.has(organization_id=current_user.organization_id)
    ).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Access request not found")
    
    if not current_user.is_superuser and request.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this request")
    
    return AccessRequestResponse(
        id=request.id,
        requester_id=request.requester_id,
        requester_name=request.requester.full_name or request.requester.email.split('@')[0],
        requester_email=request.requester.email,
        requester_department="Current Department",
        dataset_id=request.dataset_id,
        dataset_name=request.dataset.name,
        dataset_owner=request.dataset.owner.full_name or request.dataset.owner.email.split('@')[0],
        request_type=request.request_type,
        requested_level=request.requested_level,
        purpose=request.purpose,
        justification=request.justification,
        request_date=request.created_at.isoformat(),
        expiry_date=request.expiry_date.isoformat() if request.expiry_date else None,
        status=request.status,
        approved_by=request.approved_by.full_name if request.approved_by else None,
        approved_date=request.approved_date.isoformat() if request.approved_date else None,
        rejection_reason=request.rejection_reason,
        urgency=request.urgency,
        category=request.category
    )

@router.delete("/requests/{request_id}")
async def cancel_access_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a pending access request
    """
    request = db.query(AccessRequest).filter(
        AccessRequest.id == request_id,
        AccessRequest.requester_id == current_user.id,
        AccessRequest.status == RequestStatus.PENDING
    ).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Pending request not found or not authorized to cancel")
    
    db.delete(request)
    db.commit()
    
    log_audit_activity(
        db=db,
        action="REQUEST_CANCELLED",
        user_id=current_user.id,
        dataset_id=request.dataset_id,
        details="Access request cancelled by requester",
        ip_address="192.168.1.1",
        user_agent="MockAgent"
    )
    
    return {"message": "Access request cancelled successfully"}
@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False, description="Show only unread notifications"),
    limit: int = Query(50, description="Maximum number of notifications to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get notifications for the current user
    """
    query = db.query(Notification).filter(Notification.recipient_id == current_user.id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    
    result = []
    for notification in notifications:
        result.append(NotificationResponse(
            id=notification.id,
            title=notification.title,
            message=notification.message,
            notification_type=notification.notification_type,
            is_read=notification.is_read,
            created_at=notification.created_at.isoformat(),
            sender_name=notification.sender.full_name if notification.sender else None,
            related_resource_type=notification.related_resource_type,
            related_resource_id=notification.related_resource_id
        ))
    
    return result

@router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a notification as read
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Notification marked as read"}


@router.patch("/notifications/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark all notifications as read for the current user
    """
    notifications = db.query(Notification).filter(
        Notification.recipient_id == current_user.id,
        Notification.is_read == False
    ).all()
    
    for notification in notifications:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Marked {len(notifications)} notifications as read"}


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a notification
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    
    return {"message": "Notification deleted successfully"}


@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action type"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    dataset_id: Optional[int] = Query(None, description="Filter by dataset ID"),
    limit: int = Query(50, description="Maximum number of logs to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get audit logs for the organization
    """
    if not current_user.organization_id:
        return []
    
    # Build query for audit logs from user's organization
    query = db.query(AuditLog).join(User, AuditLog.user_id == User.id).filter(
        User.organization_id == current_user.organization_id
    )
    
    # Apply filters
    if action:
        query = query.filter(AuditLog.action == action)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if dataset_id:
        query = query.filter(AuditLog.dataset_id == dataset_id)
    
    # Order by timestamp descending and limit results
    audit_logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    result = []
    for log in audit_logs:
        result.append(AuditLogResponse(
            id=log.id,
            action=log.action,
            user_id=log.user_id,
            user_name=log.user.full_name or log.user.email.split('@')[0],
            dataset_id=log.dataset_id,
            dataset_name=log.dataset.name if log.dataset else "Unknown",
            timestamp=log.timestamp.isoformat(),
            details=log.details,
            ip_address=log.ip_address or "Unknown",
            user_agent=log.user_agent or "Unknown"
        ))
    
    return result

def log_audit_activity(
    db: Session,
    action: str,
    user_id: int,
    dataset_id: int,
    details: str,
    ip_address: str,
    user_agent: str
):
    """
    Log an audit activity
    """
    audit_entry = AuditLog(
        action=action,
        user_id=user_id,
        dataset_id=dataset_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(audit_entry)
    db.commit()

# Remove sample data initialization
# def initialize_sample_data():
#     """Initialize sample access requests and audit logs"""
#     
#     # Sample access requests
#     sample_requests = [
#         {
#             "id": 1,
#             "requester_id": 1,
#             "requester_name": "John Smith",
#             "requester_email": "john.smith@techcorp.com",
#             "requester_department": "Sales",
#             "dataset_id": 1,
#             "dataset_name": "Financial_Reports_Confidential_2023",
#             "dataset_owner": "Michael Chen",
#             "request_type": RequestType.ACCESS,
#             "requested_level": AccessLevel.READ,
#             "purpose": "Quarterly sales analysis and revenue forecasting",
#             "justification": "Need access to financial data to create accurate sales projections for Q1 2024.",
#             "request_date": "2024-01-15T10:30:00Z",
#             "expiry_date": "2024-03-15T10:30:00Z",
#             "status": RequestStatus.PENDING,
#             "urgency": UrgencyLevel.HIGH,
#             "category": RequestCategory.ANALYSIS
#         },
#         {
#             "id": 2,
#             "requester_id": 2,
#             "requester_name": "Lisa Wong",
#             "requester_email": "lisa.wong@techcorp.com",
#             "requester_department": "Research",
#             "dataset_id": 2,
#             "dataset_name": "Product_Development_Research_Internal",
#             "dataset_owner": "David Kim",
#             "request_type": RequestType.DOWNLOAD,
#             "requested_level": AccessLevel.READ,
#             "purpose": "Competitive analysis research project",
#             "justification": "Conducting market research study that requires analysis of product development patterns.",
#             "request_date": "2024-01-14T14:15:00Z",
#             "status": RequestStatus.APPROVED,
#             "approved_by": "David Kim",
#             "approved_date": "2024-01-15T09:20:00Z",
#             "urgency": UrgencyLevel.MEDIUM,
#             "category": RequestCategory.RESEARCH
#         }
#     ]
#     
#     # Sample audit logs
#     sample_audit_logs = [
#         {
#             "id": 1,
#             "action": "ACCESS_GRANTED",
#             "user_id": 2,
#             "user_name": "Lisa Wong",
#             "dataset_id": 2,
#             "dataset_name": "Product_Development_Research_Internal",
#             "timestamp": "2024-01-15T09:20:00Z",
#             "details": "Access granted by David Kim for research project",
#             "ip_address": "192.168.1.45",
#             "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
#         },
#         {
#             "id": 2,
#             "action": "DATA_DOWNLOADED",
#             "user_id": 2,
#             "user_name": "Lisa Wong",
#             "dataset_id": 2,
#             "dataset_name": "Product_Development_Research_Internal",
#             "timestamp": "2024-01-15T10:15:00Z",
#             "details": "Dataset downloaded following approved access request",
#             "ip_address": "192.168.1.45",
#             "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
#         },
#         {
#             "id": 3,
#             "action": "ACCESS_DENIED",
#             "user_id": 3,
#             "user_name": "Robert Taylor",
#             "dataset_id": 1,
#             "dataset_name": "Financial_Reports_Confidential_2023",
#             "timestamp": "2024-01-12T17:30:00Z",
#             "details": "Access request rejected due to insufficient clearance",
#             "ip_address": "192.168.1.78",
#             "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
#         }
#     ]
#     
#     access_requests_storage.extend(sample_requests)
#     audit_logs_storage.extend(sample_audit_logs)

# Sample data initialization removed - using real database data