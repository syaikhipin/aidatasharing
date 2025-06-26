from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from pydantic import BaseModel

router = APIRouter()

class ModelResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str
    accuracy: Optional[float] = None
    created_at: str
    updated_at: str
    organization_id: int
    created_by: int

class ModelCreate(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    name: str
    description: Optional[str] = None
    dataset_id: int
    target_column: str
    model_type: str = "classification"
    engine: str = "lightgbm"

@router.get("/", response_model=List[ModelResponse])
async def list_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List models for the user's organization"""
    if not current_user.organization_id:
        # Return empty list for users without organizations
        return []
    
    # Mock data for now - replace with actual model queries
    models = [
        ModelResponse(
            id="model_001",
            name="Customer Churn Prediction",
            description="Predicts customer churn based on usage patterns",
            status="active",
            accuracy=0.924,
            created_at="2024-01-15T10:30:00Z",
            updated_at="2024-01-15T14:22:00Z",
            organization_id=current_user.organization_id,
            created_by=current_user.id
        ),
        ModelResponse(
            id="model_002", 
            name="Sales Forecasting",
            description="Forecasts monthly sales based on historical data",
            status="training",
            accuracy=None,
            created_at="2024-01-16T09:15:00Z",
            updated_at="2024-01-16T09:15:00Z",
            organization_id=current_user.organization_id,
            created_by=current_user.id
        )
    ]
    
    return models

@router.post("/", response_model=ModelResponse)
async def create_model(
    model: ModelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new model"""
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization to create models")
    
    # Mock model creation - replace with actual MindsDB integration
    new_model = ModelResponse(
        id=f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        name=model.name,
        description=model.description,
        status="training", 
        accuracy=None,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        organization_id=current_user.organization_id,
        created_by=current_user.id
    )
    
    return new_model

@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific model"""
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Mock model data - replace with actual model retrieval
    model = ModelResponse(
        id=model_id,
        name="Sample Model",
        description="This is a sample model for testing",
        status="active",
        accuracy=0.85,
        created_at="2024-01-15T10:30:00Z",
        updated_at="2024-01-15T14:22:00Z",
        organization_id=current_user.organization_id,
        created_by=current_user.id
    )
    
    return model

@router.get("/{model_id}/status")
async def get_model_status(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get model training status"""
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {
        "model_id": model_id,
        "status": "active",
        "training_progress": 100,
        "accuracy": 0.85,
        "last_updated": datetime.now().isoformat()
    }

@router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a model"""
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Mock deletion - replace with actual model deletion
    return {"message": f"Model {model_id} deleted successfully"} 