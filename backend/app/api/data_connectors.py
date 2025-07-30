"""
Enhanced Database Connectors API endpoints
Provides endpoints for managing MySQL, PostgreSQL, S3, document processing, and other data connectors
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
import json
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.dataset import DatabaseConnector
from app.models.organization import DataSharingLevel
from app.services.mindsdb import MindsDBService
from app.services.connector_service import ConnectorService
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class DatabaseConnectorCreate(BaseModel):
    name: str
    connector_type: str  # 'mysql', 'postgresql', 's3', 'api'
    description: Optional[str] = None
    connection_config: Dict[str, Any]
    credentials: Optional[Dict[str, Any]] = None


class DatabaseConnectorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    connection_config: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


# New simplified connector model
class SimplifiedConnectorCreate(BaseModel):
    name: str
    connector_type: str
    description: Optional[str] = None
    connection_url: str


class DatasetInfo(BaseModel):
    id: int
    name: str
    type: str
    sharing_level: str
    public_share_enabled: bool

class DatabaseConnectorResponse(BaseModel):
    id: int
    name: str
    connector_type: str
    description: Optional[str]
    is_active: bool
    test_status: str
    last_tested_at: Optional[datetime]
    created_at: datetime
    mindsdb_database_name: Optional[str]
    organization_id: int
    datasets: Optional[List[DatasetInfo]] = None
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[DatabaseConnectorResponse])
async def list_connectors(
    connector_type: Optional[str] = None,
    active_only: bool = True,
    include_datasets: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List database connectors for the current organization."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must belong to an organization"
        )
    
    query = db.query(DatabaseConnector).filter(
        DatabaseConnector.organization_id == current_user.organization_id,
        DatabaseConnector.is_deleted == False
    )
    
    if active_only:
        query = query.filter(DatabaseConnector.is_active == True)
    
    if connector_type:
        query = query.filter(DatabaseConnector.connector_type == connector_type)
    
    connectors = query.order_by(DatabaseConnector.created_at.desc()).all()
    
    if include_datasets:
        # Add dataset information to connectors
        from app.models.dataset import Dataset
        result = []
        for connector in connectors:
            # Get associated datasets
            datasets = db.query(Dataset).filter(
                Dataset.connector_id == connector.id,
                Dataset.is_deleted == False
            ).all()
            
            # Create DatasetInfo objects
            dataset_infos = [
                DatasetInfo(
                    id=dataset.id,
                    name=dataset.name,
                    type=dataset.type.value,  # Convert enum to string
                    sharing_level=dataset.sharing_level.value,  # Convert enum to string
                    public_share_enabled=dataset.public_share_enabled
                )
                for dataset in datasets
            ]
            
            # Create response object with datasets
            connector_response = DatabaseConnectorResponse(
                id=connector.id,
                name=connector.name,
                connector_type=connector.connector_type,
                description=connector.description,
                is_active=connector.is_active,
                test_status=connector.test_status,
                last_tested_at=connector.last_tested_at,
                created_at=connector.created_at,
                mindsdb_database_name=connector.mindsdb_database_name,
                organization_id=connector.organization_id,
                datasets=dataset_infos
            )
            
            result.append(connector_response)
        
        return result
    
    return connectors


@router.post("/", response_model=DatabaseConnectorResponse)
async def create_connector(
    connector_data: DatabaseConnectorCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new database connector."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must belong to an organization"
        )
    
    # Validate connector type
    supported_types = ['mysql', 'postgresql', 's3', 'api', 'mongodb', 'clickhouse']
    if connector_data.connector_type not in supported_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported connector type. Supported: {supported_types}"
        )
    
    # Check for duplicate names in organization
    existing = db.query(DatabaseConnector).filter(
        DatabaseConnector.organization_id == current_user.organization_id,
        DatabaseConnector.name == connector_data.name,
        DatabaseConnector.is_deleted == False
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connector with this name already exists"
        )
    
    # Create connector
    db_connector = DatabaseConnector(
        name=connector_data.name,
        connector_type=connector_data.connector_type,
        description=connector_data.description,
        organization_id=current_user.organization_id,
        connection_config=connector_data.connection_config,
        credentials=connector_data.credentials,  # TODO: Encrypt in production
        created_by=current_user.id,
        mindsdb_database_name=f"org_{current_user.organization_id}_{connector_data.name.lower().replace(' ', '_')}"
    )
    
    db.add(db_connector)
    db.commit()
    db.refresh(db_connector)
    
    # Test connection in background
    background_tasks.add_task(test_connector_connection, db_connector.id)
    
    return DatabaseConnectorResponse(
        id=db_connector.id,
        name=db_connector.name,
        connector_type=db_connector.connector_type,
        description=db_connector.description,
        is_active=db_connector.is_active,
        test_status=db_connector.test_status,
        last_tested_at=db_connector.last_tested_at,
        created_at=db_connector.created_at,
        mindsdb_database_name=db_connector.mindsdb_database_name,
        organization_id=db_connector.organization_id
    )


@router.post("/simplified", response_model=DatabaseConnectorResponse)
async def create_simplified_connector(
    connector_data: SimplifiedConnectorCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new database connector using simplified URL input."""
    from app.utils.connection_parser import parse_connection_url, ConnectionParseError
    
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must belong to an organization"
        )
    
    # Validate connector type
    supported_types = ['mysql', 'postgresql', 's3', 'api', 'mongodb', 'clickhouse']
    if connector_data.connector_type not in supported_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported connector type. Supported: {supported_types}"
        )
    
    # Parse connection URL
    try:
        connection_config, credentials = parse_connection_url(
            connector_data.connection_url, 
            connector_data.connector_type
        )
    except ConnectionParseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid connection URL: {str(e)}"
        )
    
    # Check for duplicate names in organization
    existing = db.query(DatabaseConnector).filter(
        DatabaseConnector.organization_id == current_user.organization_id,
        DatabaseConnector.name == connector_data.name,
        DatabaseConnector.is_deleted == False
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connector with this name already exists"
        )
    
    # Create connector using parsed configuration
    db_connector = DatabaseConnector(
        name=connector_data.name,
        connector_type=connector_data.connector_type,
        description=connector_data.description,
        organization_id=current_user.organization_id,
        connection_config=connection_config,
        credentials=credentials,  # TODO: Encrypt in production
        created_by=current_user.id,
        mindsdb_database_name=f"org_{current_user.organization_id}_{connector_data.name.lower().replace(' ', '_')}"
    )
    
    db.add(db_connector)
    db.commit()
    db.refresh(db_connector)
    
    # Test connection in background
    background_tasks.add_task(test_connector_connection, db_connector.id)
    
    return DatabaseConnectorResponse(
        id=db_connector.id,
        name=db_connector.name,
        connector_type=db_connector.connector_type,
        description=db_connector.description,
        is_active=db_connector.is_active,
        test_status=db_connector.test_status,
        last_tested_at=db_connector.last_tested_at,
        created_at=db_connector.created_at,
        mindsdb_database_name=db_connector.mindsdb_database_name,
        organization_id=db_connector.organization_id
    )


@router.get("/{connector_id}", response_model=DatabaseConnectorResponse)
async def get_connector(
    connector_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific database connector."""
    connector = db.query(DatabaseConnector).filter(
        DatabaseConnector.id == connector_id,
        DatabaseConnector.organization_id == current_user.organization_id,
        DatabaseConnector.is_deleted == False
    ).first()
    
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    return connector


@router.put("/{connector_id}", response_model=DatabaseConnectorResponse)
async def update_connector(
    connector_id: int,
    connector_update: DatabaseConnectorUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a database connector."""
    connector = db.query(DatabaseConnector).filter(
        DatabaseConnector.id == connector_id,
        DatabaseConnector.organization_id == current_user.organization_id,
        DatabaseConnector.is_deleted == False
    ).first()
    
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    # Update fields
    update_data = connector_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(connector, field, value)
    
    connector.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(connector)
    
    # Re-test connection if config changed
    if connector_update.connection_config or connector_update.credentials:
        background_tasks.add_task(test_connector_connection, connector_id)
    
    return connector


@router.delete("/{connector_id}")
async def delete_connector(
    connector_id: int,
    force_delete: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a database connector."""
    connector = db.query(DatabaseConnector).filter(
        DatabaseConnector.id == connector_id,
        DatabaseConnector.organization_id == current_user.organization_id,
        DatabaseConnector.is_deleted == False
    ).first()
    
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    if force_delete and current_user.is_superuser:
        # Hard delete
        db.delete(connector)
    else:
        # Soft delete
        connector.soft_delete(current_user.id)
    
    db.commit()
    
    return {"message": "Connector deleted successfully"}


@router.post("/{connector_id}/test")
async def test_connector(
    connector_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test database connector connection."""
    connector = db.query(DatabaseConnector).filter(
        DatabaseConnector.id == connector_id,
        DatabaseConnector.organization_id == current_user.organization_id,
        DatabaseConnector.is_deleted == False
    ).first()
    
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    # Test connection
    result = await test_connector_connection_sync(connector)
    
    # Update test results
    connector.test_status = "success" if result["success"] else "failed"
    connector.test_error = result.get("error")
    connector.last_tested_at = datetime.utcnow()
    
    db.commit()
    
    return result


@router.post("/{connector_id}/sync")
async def sync_with_mindsdb(
    connector_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sync connector with MindsDB."""
    connector = db.query(DatabaseConnector).filter(
        DatabaseConnector.id == connector_id,
        DatabaseConnector.organization_id == current_user.organization_id,
        DatabaseConnector.is_deleted == False
    ).first()
    
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    # Sync with MindsDB in background
    background_tasks.add_task(sync_connector_with_mindsdb, connector_id)
    
    return {
        "message": "Connector sync with MindsDB started",
        "mindsdb_database_name": connector.mindsdb_database_name
    }


class CreateDatasetFromConnector(BaseModel):
    dataset_name: str
    description: Optional[str] = None
    table_or_endpoint: Optional[str] = None  # For API connectors, this can be a different endpoint
    sharing_level: str = "private"


@router.post("/{connector_id}/create-dataset")
async def create_dataset_from_connector(
    connector_id: int,
    dataset_data: CreateDatasetFromConnector,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a dataset from a connector."""
    connector = db.query(DatabaseConnector).filter(
        DatabaseConnector.id == connector_id,
        DatabaseConnector.organization_id == current_user.organization_id,
        DatabaseConnector.is_deleted == False
    ).first()
    
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    if connector.test_status != "success":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connector must be successfully tested before creating datasets"
        )
    
    # For API connectors, create dataset with API data
    if connector.connector_type == "api":
        result = await _create_api_dataset(connector, dataset_data, current_user.id)
    else:
        # For database connectors, use the connector service
        connector_service = ConnectorService(db)
        
        # Map sharing level string to enum
        from app.models.organization import DataSharingLevel
        sharing_level_map = {
            "private": DataSharingLevel.PRIVATE,
            "organization": DataSharingLevel.ORGANIZATION,
            "public": DataSharingLevel.PUBLIC
        }
        sharing_level = sharing_level_map.get(dataset_data.sharing_level.lower(), DataSharingLevel.PRIVATE)
        
        result = await connector_service.create_connector_dataset(
            connector=connector,
            table_or_query=dataset_data.table_or_endpoint or "default_table",
            dataset_name=dataset_data.dataset_name,
            user_id=current_user.id,
            description=dataset_data.description,
            sharing_level=sharing_level
        )
    
    if result.get("success"):
        return {
            "message": "Dataset created successfully",
            "dataset_id": result.get("dataset_id"),
            "dataset_name": result.get("dataset_name")
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to create dataset")
        )


@router.post("/image-remote")
async def create_remote_image_connector(
    connector_config: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a remote image data connector (S3, URL, FTP, etc.)"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must belong to an organization"
        )
    
    try:
        # Validate required fields
        required_fields = ["name", "source_type", "connection_params"]
        for field in required_fields:
            if field not in connector_config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        connector_name = connector_config["name"]
        source_type = connector_config["source_type"]
        connection_params = connector_config["connection_params"]
        
        # Create database connector record
        connector = DatabaseConnector(
            name=connector_name,
            connector_type="image_remote",
            description=f"Remote image connector for {source_type}",
            connection_config={
                "source_type": source_type,
                "connection_params": connection_params
            },
            organization_id=current_user.organization_id,
            created_by=current_user.id,
            mindsdb_database_name=f"image_remote_{connector_name.lower().replace(' ', '_')}"
        )
        
        db.add(connector)
        db.commit()
        db.refresh(connector)
        
        # Create MindsDB handler
        connector_service = ConnectorService(db)
        handler_result = connector_service.create_image_remote_handler(connector)
        
        if handler_result["success"]:
            connector.test_status = "connected"
            connector.last_tested_at = datetime.utcnow()
            db.commit()
            
            return {
                "success": True,
                "message": "Remote image connector created successfully",
                "connector_id": connector.id,
                "connector_name": connector_name,
                "source_type": source_type,
                "mindsdb_handler": handler_result.get("handler_name")
            }
        else:
            # Rollback if handler creation failed
            db.delete(connector)
            db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create MindsDB handler: {handler_result.get('error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remote image connector creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Remote image connector creation failed: {str(e)}"
        )

    
    if result.get("success"):
        return {
            "message": "Dataset created successfully",
            "dataset_id": result.get("dataset_id"),
            "dataset_name": result.get("dataset_name")
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to create dataset")
        )


async def test_connector_connection_sync(connector: DatabaseConnector) -> Dict[str, Any]:
    """Test connector connection synchronously."""
    try:
        if connector.connector_type == "mysql":
            return await _test_mysql_connection(connector)
        elif connector.connector_type == "postgresql":
            return await _test_postgresql_connection(connector)
        elif connector.connector_type == "s3":
            return await _test_s3_connection(connector)
        elif connector.connector_type == "mongodb":
            return await _test_mongodb_connection(connector)
        elif connector.connector_type == "api":
            return await _test_api_connection(connector)
        else:
            return {"success": False, "error": f"Testing not implemented for {connector.connector_type}"}
            
    except Exception as e:
        logger.error(f"Connector test failed for {connector.id}: {e}")
        return {"success": False, "error": str(e)}


async def test_connector_connection(connector_id: int):
    """Background task to test connector connection."""
    # This would be implemented with proper database session handling
    # For now, it's a placeholder
    logger.info(f"Testing connector {connector_id} connection in background")


async def sync_connector_with_mindsdb(connector_id: int):
    """Background task to sync connector with MindsDB."""
    logger.info(f"Syncing connector {connector_id} with MindsDB in background")


async def _test_mysql_connection(connector: DatabaseConnector) -> Dict[str, Any]:
    """Test MySQL connection."""
    try:
        import mysql.connector
        
        config = connector.connection_config.copy()
        if connector.credentials:
            config.update(connector.credentials)
        
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return {"success": True, "message": "MySQL connection successful"}
        
    except Exception as e:
        return {"success": False, "error": f"MySQL connection failed: {str(e)}"}


async def _test_postgresql_connection(connector: DatabaseConnector) -> Dict[str, Any]:
    """Test PostgreSQL connection."""
    try:
        import psycopg2
        
        config = connector.connection_config.copy()
        if connector.credentials:
            config.update(connector.credentials)
        
        connection = psycopg2.connect(**config)
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return {"success": True, "message": "PostgreSQL connection successful"}
        
    except Exception as e:
        return {"success": False, "error": f"PostgreSQL connection failed: {str(e)}"}


async def _test_s3_connection(connector: DatabaseConnector) -> Dict[str, Any]:
    """Test S3 connection."""
    try:
        import boto3
        
        config = connector.connection_config.copy()
        if connector.credentials:
            config.update(connector.credentials)
        
        s3_client = boto3.client('s3', **config)
        response = s3_client.list_buckets()
        
        return {"success": True, "message": "S3 connection successful", "bucket_count": len(response['Buckets'])}
        
    except Exception as e:
        return {"success": False, "error": f"S3 connection failed: {str(e)}"}


async def _test_mongodb_connection(connector: DatabaseConnector) -> Dict[str, Any]:
    """Test MongoDB connection."""
    try:
        from pymongo import MongoClient
        
        config = connector.connection_config.copy()
        if connector.credentials:
            config.update(connector.credentials)
        
        client = MongoClient(**config)
        # Test connection
        client.server_info()
        client.close()
        
        return {"success": True, "message": "MongoDB connection successful"}
        
    except Exception as e:
        return {"success": False, "error": f"MongoDB connection failed: {str(e)}"}


async def _test_api_connection(connector: DatabaseConnector) -> Dict[str, Any]:
    """Test API connection."""
    try:
        import requests
        
        config = connector.connection_config.copy()
        
        # Apply SSL configuration for development
        from app.core.config import settings
        from urllib.parse import urlparse
        
        base_url = config.get("base_url", "")
        parsed_url = urlparse(base_url)
        host = parsed_url.hostname
        port = parsed_url.port
        
        # Get SSL-aware configuration
        ssl_config = settings.get_ssl_config_for_connector(
            'api', host, port, config
        )
        config.update(ssl_config)
        
        # Use potentially modified base_url
        base_url = config.get("base_url", base_url)
        endpoint = config.get("endpoint", "")
        method = config.get("method", "GET").upper()
        timeout = config.get("timeout", 30)
        headers = config.get("headers", {})
        ssl_verify = config.get("ssl_verify", True)
        
        if not base_url or not endpoint:
            return {"success": False, "error": "Base URL and endpoint are required"}
        
        full_url = f"{base_url.rstrip('/')}{endpoint}"
        
        # Make the API request with SSL configuration
        response = requests.request(
            method=method,
            url=full_url,
            headers=headers,
            timeout=timeout,
            verify=ssl_verify
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                data_count = len(data) if isinstance(data, list) else 1
                return {
                    "success": True, 
                    "message": f"API connection successful. Retrieved {data_count} items.",
                    "status_code": response.status_code,
                    "data_preview": str(data)[:200] + "..." if len(str(data)) > 200 else str(data),
                    "ssl_config": {"ssl_verify": ssl_verify, "protocol": "HTTP" if not ssl_verify else "HTTPS"}
                }
            except:
                return {
                    "success": True,
                    "message": f"API connection successful. Response received (non-JSON).",
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", "unknown"),
                    "ssl_config": {"ssl_verify": ssl_verify, "protocol": "HTTP" if not ssl_verify else "HTTPS"}
                }
        else:
            return {
                "success": False, 
                "error": f"API request failed with status {response.status_code}: {response.text[:200]}"
            }
        
    except requests.exceptions.Timeout:
        return {"success": False, "error": "API request timed out"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Failed to connect to API endpoint"}
    except Exception as e:
        return {"success": False, "error": f"API connection failed: {str(e)}"}


async def _create_api_dataset(
    connector: DatabaseConnector, 
    dataset_data: CreateDatasetFromConnector, 
    user_id: int
) -> Dict[str, Any]:
    """Create a dataset from API connector data."""
    try:
        import requests
        from app.models.dataset import Dataset, DatasetType, DatasetStatus
        from app.core.database import get_db
        
        # Get database session
        db = next(get_db())
        
        config = connector.connection_config.copy()
        base_url = config.get("base_url", "")
        
        # Use custom endpoint if provided, otherwise use connector's default
        endpoint = dataset_data.table_or_endpoint or config.get("endpoint", "")
        method = config.get("method", "GET").upper()
        timeout = config.get("timeout", 30)
        headers = config.get("headers", {})
        
        full_url = f"{base_url.rstrip('/')}{endpoint}"
        
        # Fetch data from API
        response = requests.request(
            method=method,
            url=full_url,
            headers=headers,
            timeout=timeout
        )
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"API request failed with status {response.status_code}"
            }
        
        # Parse JSON data
        try:
            api_data = response.json()
        except:
            return {
                "success": False,
                "error": "API response is not valid JSON"
            }
        
        # Determine data characteristics
        data_count = len(api_data) if isinstance(api_data, list) else 1
        sample_data = api_data[:5] if isinstance(api_data, list) else [api_data]
        
        # Create schema information
        schema_info = {}
        if sample_data and len(sample_data) > 0:
            first_item = sample_data[0]
            if isinstance(first_item, dict):
                schema_info = {
                    "columns": [{"name": key, "type": type(value).__name__} for key, value in first_item.items()],
                    "sample_data": sample_data,
                    "api_endpoint": full_url,
                    "total_items": data_count
                }
        
        # Map sharing level
        sharing_level_map = {
            "private": DataSharingLevel.PRIVATE,
            "organization": DataSharingLevel.ORGANIZATION,
            "public": DataSharingLevel.PUBLIC
        }
        sharing_level = sharing_level_map.get(dataset_data.sharing_level.lower(), DataSharingLevel.PRIVATE)
        
        # Create dataset record
        dataset = Dataset(
            name=dataset_data.dataset_name,
            description=dataset_data.description or f"API dataset from {connector.name}",
            type=DatasetType.API,
            status=DatasetStatus.ACTIVE,
            owner_id=user_id,
            organization_id=connector.organization_id,
            sharing_level=sharing_level,
            connector_id=connector.id,
            source_url=full_url,
            row_count=data_count,
            column_count=len(schema_info.get("columns", [])),
            schema_info=schema_info,
            allow_download=True,
            allow_api_access=True,
            allow_ai_chat=True,
            # Store API data context for chat
            chat_context={
                "api_endpoint": full_url,
                "data_sample": sample_data,
                "total_items": data_count,
                "connector_name": connector.name,
                "schema": schema_info.get("columns", [])
            }
        )
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        logger.info(f"✅ Created API dataset: {dataset_data.dataset_name} (ID: {dataset.id})")
        
        return {
            "success": True,
            "dataset_id": dataset.id,
            "dataset_name": dataset_data.dataset_name,
            "api_endpoint": full_url,
            "data_count": data_count
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to create API dataset: {e}")
        return {
            "success": False,
            "error": str(e)
        } 