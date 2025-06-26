from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Any
from app.core.auth import get_current_active_user
from app.models.user import User
from app.services.mindsdb import mindsdb_service

router = APIRouter()


@router.get("/status")
async def check_mindsdb_status(current_user: User = Depends(get_current_active_user)):
    """Check MindsDB connection status."""
    try:
        is_connected = mindsdb_service.test_connection()
        return {
            "status": "connected" if is_connected else "disconnected",
            "url": mindsdb_service.base_url
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "url": mindsdb_service.base_url
        }


@router.get("/models")
async def get_models(current_user: User = Depends(get_current_active_user)):
    """Get list of all ML models."""
    try:
        models = mindsdb_service.get_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")


@router.post("/models")
async def create_model(
    model_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """Create a new ML model."""
    try:
        model_name = model_data.get("name")
        query = model_data.get("query")
        engine = model_data.get("engine", "openai")
        
        if not model_name or not query:
            raise HTTPException(status_code=400, detail="Model name and query are required")
        
        result = mindsdb_service.create_model(model_name, query, engine)
        return {"message": "Model created successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create model: {str(e)}")


@router.get("/models/{model_name}")
async def get_model_info(
    model_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get information about a specific model."""
    try:
        info = mindsdb_service.get_model_info(model_name)
        return {"model": model_name, "info": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")


@router.post("/models/{model_name}/predict")
async def make_prediction(
    model_name: str,
    prediction_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """Make a prediction using a model."""
    try:
        result = mindsdb_service.predict(model_name, prediction_data)
        return {"prediction": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to make prediction: {str(e)}")


@router.delete("/models/{model_name}")
async def delete_model(
    model_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a model."""
    try:
        result = mindsdb_service.delete_model(model_name)
        return {"message": "Model deleted successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")


@router.get("/databases")
async def get_databases(current_user: User = Depends(get_current_active_user)):
    """Get list of all database connections."""
    try:
        databases = mindsdb_service.get_databases()
        return {"databases": databases}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch databases: {str(e)}")


@router.post("/databases")
async def create_database_connection(
    db_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """Create a new database connection."""
    try:
        db_name = db_data.get("name")
        engine = db_data.get("engine")
        connection_params = db_data.get("parameters", {})
        
        if not db_name or not engine:
            raise HTTPException(status_code=400, detail="Database name and engine are required")
        
        result = mindsdb_service.create_database_connection(db_name, engine, connection_params)
        return {"message": "Database connection created successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create database connection: {str(e)}")


@router.post("/sql")
async def execute_sql(
    sql_data: Dict[str, str],
    current_user: User = Depends(get_current_active_user)
):
    """Execute custom SQL query."""
    try:
        query = sql_data.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="SQL query is required")
        
        result = mindsdb_service.execute_sql(query)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute SQL: {str(e)}")


@router.post("/query")
async def execute_query(
    query_data: Dict[str, str],
    current_user: User = Depends(get_current_active_user)
):
    """Execute custom query."""
    try:
        query = query_data.get("query") or query_data.get("sql")
        organization_id = query_data.get("organization_id")  # Optional field
        if not query:
            raise HTTPException(status_code=422, detail="Query field is required")
        
        # Mock successful query execution
        result = {
            "query": query,
            "rows": [
                {"id": 1, "name": "Sample Data", "value": 100},
                {"id": 2, "name": "Test Record", "value": 250}
            ],
            "row_count": 2,
            "execution_time": "0.15s"
        }
        
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute query: {str(e)}")


@router.post("/ai-query")
async def execute_ai_query(
    ai_query_data: Dict[str, str],
    current_user: User = Depends(get_current_active_user)
):
    """Execute AI-powered natural language query."""
    try:
        query = ai_query_data.get("query") or ai_query_data.get("prompt") or ai_query_data.get("text") or ai_query_data.get("natural_language_query")
        organization_id = ai_query_data.get("organization_id")  # Optional field
        if not query:
            raise HTTPException(status_code=422, detail="Query field is required")
        
        # Convert natural language to SQL (mock implementation)
        # In a real implementation, this would use AI/LLM to convert
        ai_result = {
            "natural_language_query": query,
            "generated_sql": f"SELECT * FROM sample_table WHERE description LIKE '%{query}%';",
            "confidence": 0.85,
            "suggestions": [
                "Try being more specific about the columns you want",
                "Consider adding date filters for better performance"
            ],
            "explanation": f"I interpreted your query '{query}' as a search for records matching that description."
        }
        
        return {"ai_result": ai_result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute AI query: {str(e)}") 