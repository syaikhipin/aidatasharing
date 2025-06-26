from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.dataset import Dataset
from app.models.analytics import ActivityLog, UsageMetric, DatashareStats, UserSessionLog, ModelPerformanceLog
from app.core.auth import get_current_user

router = APIRouter()

# Analytics Response Models
class OrganizationStatsResponse(BaseModel):
    id: int
    name: str
    total_users: int
    total_datasets: int
    total_models: int
    storage_used: float  # GB
    storage_limit: float  # GB

class UsageStatsResponse(BaseModel):
    total_api_calls: int
    total_predictions: int
    average_response_time: float  # ms
    uptime: float  # percentage

class TrendDataPoint(BaseModel):
    date: str
    count: int
    active_users: Optional[int] = None

class TrendsResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    dataset_uploads: List[TrendDataPoint]
    model_creations: List[TrendDataPoint]
    predictions: List[TrendDataPoint]
    user_activity: List[TrendDataPoint]

class ModelPerformanceResponse(BaseModel):
    id: str
    name: str
    accuracy: float
    predictions: int
    last_updated: str
    status: str

class UserActivityResponse(BaseModel):
    user_id: int
    name: str
    last_active: str
    actions_today: int
    role: str
    department: str

class DatasetUsageResponse(BaseModel):
    id: int
    name: str
    access_count: int
    last_accessed: str
    sharing_level: str

class StorageByDepartmentResponse(BaseModel):
    department: str
    storage: float
    percentage: float

class DataUsageResponse(BaseModel):
    most_accessed_datasets: List[DatasetUsageResponse]
    storage_by_department: List[StorageByDepartmentResponse]

class CostCategoryResponse(BaseModel):
    category: str
    amount: float
    percentage: float

class CostAnalysisResponse(BaseModel):
    total_cost: float
    cost_by_category: List[CostCategoryResponse]
    projected_monthly_cost: float

class AnalyticsResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    organization: OrganizationStatsResponse
    usage: UsageStatsResponse
    trends: TrendsResponse
    model_performance: List[ModelPerformanceResponse]
    user_activity: List[UserActivityResponse]
    data_usage: DataUsageResponse
    costs: CostAnalysisResponse

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics data for the user's organization
    """
    if not current_user.organization_id:
        # Return mock data for users without organizations
        return AnalyticsResponse(
            organization=OrganizationStatsResponse(
                id=0,
                name="Demo Organization",
                total_users=1,
                total_datasets=0,
                total_models=0,
                storage_used=0.0,
                storage_limit=100.0
            ),
            usage=UsageStatsResponse(
                total_api_calls=0,
                total_predictions=0,
                average_response_time=0.0,
                uptime=100.0
            ),
            trends=TrendsResponse(
                dataset_uploads=[],
                model_creations=[],
                predictions=[],
                user_activity=[]
            ),
            model_performance=[],
            user_activity=[],
            data_usage=DataUsageResponse(
                most_accessed_datasets=[],
                storage_by_department=[]
            ),
            costs=CostAnalysisResponse(
                total_cost=0.0,
                cost_by_category=[],
                projected_monthly_cost=0.0
            )
        )
    
    # Set default date range if not provided
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    organization = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Organization Statistics
    org_users_count = db.query(User).filter(
        User.organization_id == current_user.organization_id
    ).count()
    
    org_datasets_count = db.query(Dataset).filter(
        Dataset.organization_id == current_user.organization_id
    ).count()
    
    # Calculate total storage used (mock calculation)
    total_storage_used = db.query(func.sum(Dataset.size)).filter(
        Dataset.organization_id == current_user.organization_id
    ).scalar() or 0.0
    total_storage_used = total_storage_used / (1024**3)  # Convert to GB
    
    org_stats = OrganizationStatsResponse(
        id=organization.id,
        name=organization.name,
        total_users=org_users_count,
        total_datasets=org_datasets_count,
        total_models=15,  # Mock data - replace with actual model count
        storage_used=round(total_storage_used, 2),
        storage_limit=500.0  # Mock limit
    )
    
    # Usage Statistics (mock data - replace with actual metrics)
    usage_stats = UsageStatsResponse(
        total_api_calls=45678,
        total_predictions=123456,
        average_response_time=245.0,
        uptime=99.7
    )
    
    # Trends Data
    trends_data = get_trends_data(db, current_user.organization_id, start_dt, end_dt)
    
    # Model Performance (mock data)
    model_performance = [
        ModelPerformanceResponse(
            id="model_001",
            name="Customer Churn Prediction",
            accuracy=0.924,
            predictions=15847,
            last_updated="2024-01-15T14:22:00Z",
            status="excellent"
        ),
        ModelPerformanceResponse(
            id="model_002",
            name="Sales Forecasting",
            accuracy=0.887,
            predictions=8932,
            last_updated="2024-01-14T09:15:00Z",
            status="good"
        ),
        ModelPerformanceResponse(
            id="model_003",
            name="Demand Prediction",
            accuracy=0.756,
            predictions=3421,
            last_updated="2024-01-12T16:45:00Z",
            status="needs_attention"
        )
    ]
    
    # User Activity
    user_activity_data = get_user_activity(db, current_user.organization_id, start_dt, end_dt)
    
    # Data Usage
    data_usage = get_data_usage_stats(db, current_user.organization_id)
    
    # Cost Analysis (mock data)
    cost_analysis = CostAnalysisResponse(
        total_cost=2847.50,
        cost_by_category=[
            CostCategoryResponse(category="Storage", amount=1245.30, percentage=43.7),
            CostCategoryResponse(category="API Calls", amount=892.15, percentage=31.3),
            CostCategoryResponse(category="Model Training", amount=456.78, percentage=16.0),
            CostCategoryResponse(category="Data Processing", amount=253.27, percentage=8.9)
        ],
        projected_monthly_cost=8542.50
    )
    
    return AnalyticsResponse(
        organization=org_stats,
        usage=usage_stats,
        trends=trends_data,
        model_performance=model_performance,
        user_activity=user_activity_data,
        data_usage=data_usage,
        costs=cost_analysis
    )

def get_trends_data(db: Session, organization_id: int, start_date: datetime, end_date: datetime) -> TrendsResponse:
    """Generate trends data for the specified date range"""
    
    # Dataset uploads trend
    dataset_uploads = []
    model_creations = []
    predictions = []
    user_activity = []
    
    # Generate daily data points for the date range
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Mock data generation - replace with actual queries
        dataset_uploads.append(TrendDataPoint(
            date=date_str,
            count=max(1, int((current_date.timestamp() % 25)))
        ))
        
        model_creations.append(TrendDataPoint(
            date=date_str,
            count=max(1, int((current_date.timestamp() % 7)))
        ))
        
        predictions.append(TrendDataPoint(
            date=date_str,
            count=max(100, int((current_date.timestamp() % 2000)))
        ))
        
        user_activity.append(TrendDataPoint(
            date=date_str,
            count=0,  # Not used for user activity
            active_users=max(10, int((current_date.timestamp() % 100)))
        ))
        
        current_date += timedelta(days=1)
    
    return TrendsResponse(
        dataset_uploads=dataset_uploads[-7:],  # Last 7 days
        model_creations=model_creations[-7:],
        predictions=predictions[-7:],
        user_activity=user_activity[-7:]
    )

def get_user_activity(db: Session, organization_id: int, start_date: datetime, end_date: datetime) -> List[UserActivityResponse]:
    """Get user activity data for the organization"""
    
    users = db.query(User).filter(
        User.organization_id == organization_id
    ).limit(10).all()
    
    activity_data = []
    for user in users:
        # Mock activity data - replace with actual activity tracking
        activity_data.append(UserActivityResponse(
            user_id=user.id,
            name=user.full_name or user.email.split('@')[0],
            last_active=datetime.now().isoformat(),
            actions_today=max(1, user.id % 50),
            role="Data Scientist",  # Mock role
            department="Analytics"  # Mock department
        ))
    
    return activity_data

def get_data_usage_stats(db: Session, organization_id: int) -> DataUsageResponse:
    """Get data usage statistics for the organization"""
    
    # Most accessed datasets
    datasets = db.query(Dataset).filter(
        Dataset.organization_id == organization_id
    ).limit(5).all()
    
    most_accessed = []
    for dataset in datasets:
        # Mock access count - replace with actual tracking
        most_accessed.append(DatasetUsageResponse(
            id=dataset.id,
            name=dataset.name,
            access_count=max(10, dataset.id * 23),
            last_accessed=datetime.now().isoformat(),
            sharing_level=dataset.sharing_level
        ))
    
    # Storage by department (mock data)
    storage_by_dept = [
        StorageByDepartmentResponse(department="Analytics", storage=89.4, percentage=36.4),
        StorageByDepartmentResponse(department="Engineering", storage=67.2, percentage=27.3),
        StorageByDepartmentResponse(department="Marketing", storage=45.8, percentage=18.6),
        StorageByDepartmentResponse(department="IT", storage=28.9, percentage=11.8),
        StorageByDepartmentResponse(department="Sales", storage=14.4, percentage=5.9)
    ]
    
    return DataUsageResponse(
        most_accessed_datasets=most_accessed,
        storage_by_department=storage_by_dept
    )

@router.get("/analytics/export")
async def export_analytics_report(
    format: str = Query("csv", description="Export format: csv, json, excel"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export analytics report in specified format
    """
    # Implementation for exporting analytics data
    # This would generate and return downloadable files
    
    return {
        "message": "Analytics report export initiated",
        "format": format,
        "start_date": start_date,
        "end_date": end_date,
        "download_url": f"/analytics/download/{format}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }

@router.post("/analytics/activity")
async def log_activity(
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log user activity for analytics tracking
    """
    
    activity_log = ActivityLog(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        timestamp=datetime.utcnow(),
        ip_address="0.0.0.0",  # Would be extracted from request
        user_agent="unknown"   # Would be extracted from request headers
    )
    
    db.add(activity_log)
    db.commit()
    
    return {"message": "Activity logged successfully"}

@router.get("/analytics/real-time")
async def get_real_time_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get real-time analytics metrics for dashboard widgets
    """
    
    if not current_user.organization_id:
        # Return demo data for users without organizations
        return {
            "active_users_now": 1,
            "api_calls_last_hour": 0,
            "predictions_last_hour": 0,
            "system_load": 0.1,
            "database_connections": 1,
            "cache_hit_rate": 100.0,
            "average_response_time": 50.0,
            "error_rate": 0.0,
            "timestamp": datetime.now().isoformat()
        }
    
    # Real-time metrics (mock data)
    return {
        "active_users_now": 23,
        "api_calls_last_hour": 1247,
        "predictions_last_hour": 543,
        "system_load": 67.8,
        "database_connections": 12,
        "cache_hit_rate": 94.2,
        "average_response_time": 156.7,
        "error_rate": 0.12,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/analytics/performance/{model_id}")
async def get_model_performance_details(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed performance metrics for a specific model
    """
    
    # Mock detailed model performance data
    return {
        "model_id": model_id,
        "accuracy_history": [
            {"date": "2024-01-10", "accuracy": 0.891},
            {"date": "2024-01-11", "accuracy": 0.898},
            {"date": "2024-01-12", "accuracy": 0.912},
            {"date": "2024-01-13", "accuracy": 0.924},
            {"date": "2024-01-14", "accuracy": 0.919},
            {"date": "2024-01-15", "accuracy": 0.924}
        ],
        "prediction_volume": [
            {"date": "2024-01-10", "count": 1250},
            {"date": "2024-01-11", "count": 1340},
            {"date": "2024-01-12", "count": 1567},
            {"date": "2024-01-13", "count": 1623},
            {"date": "2024-01-14", "count": 1489},
            {"date": "2024-01-15", "count": 1578}
        ],
        "response_times": [
            {"date": "2024-01-10", "avg_ms": 234},
            {"date": "2024-01-11", "avg_ms": 267},
            {"date": "2024-01-12", "avg_ms": 198},
            {"date": "2024-01-13", "avg_ms": 245},
            {"date": "2024-01-14", "avg_ms": 289},
            {"date": "2024-01-15", "avg_ms": 223}
        ],
        "error_rates": [
            {"date": "2024-01-10", "rate": 0.23},
            {"date": "2024-01-11", "rate": 0.18},
            {"date": "2024-01-12", "rate": 0.15},
            {"date": "2024-01-13", "rate": 0.12},
            {"date": "2024-01-14", "rate": 0.19},
            {"date": "2024-01-15", "rate": 0.14}
        ]
    } 