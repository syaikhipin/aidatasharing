"""
Multi-Port Proxy Service for AI Share Platform
Provides dedicated proxy ports for different database types and APIs
"""

import asyncio
import logging
import json
import urllib.parse
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uvicorn
from sqlalchemy.orm import Session
import mysql.connector
import psycopg2
import pymongo
from clickhouse_driver import Client as ClickHouseClient

# Import from main backend
import sys
import os
from pathlib import Path

# Add the parent directory to Python path dynamically
parent_dir = Path(__file__).parent.parent.resolve()
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from app.core.database import get_db
from app.models.proxy_connector import ProxyConnector, SharedProxyLink
from app.services.proxy_service import ProxyService
from app.core.app_config import get_app_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get configuration from centralized config
app_config = get_app_config()
PROXY_PORTS = app_config.proxy.get_proxy_ports()

class MultiPortProxyService:
    """Multi-port proxy service for different database types"""
    
    def __init__(self):
        self.proxy_service = ProxyService()
        self.apps = {}
        self.servers = {}
        
    def create_proxy_app(self, proxy_type: str, port: int) -> FastAPI:
        """Create a FastAPI app for a specific proxy type"""
        
        app = FastAPI(
            title=f"{proxy_type.upper()} Proxy Service",
            description=f"Dedicated proxy service for {proxy_type} connections",
            version="1.0.0"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "proxy_type": proxy_type,
                "port": port,
                "timestamp": datetime.now().isoformat()
            }
        
        @app.get("/")
        async def root():
            return {
                "message": f"{proxy_type.upper()} Proxy Service",
                "proxy_type": proxy_type,
                "port": port,
                "endpoints": [
                    f"/{proxy_type}/<database_name>",
                    f"/share/<share_id>",
                    "/health"
                ]
            }
        
        # API-specific endpoint for API proxy type
        if proxy_type == "api":
            @app.get("/api/{api_name}")
            @app.post("/api/{api_name}")
            async def proxy_api_access(
                api_name: str,
                request: Request,
                token: Optional[str] = None,
                db: Session = Depends(get_db)
            ):
                """Handle API access through proxy"""
                
                # Get token from query params or headers
                if not token:
                    token = request.query_params.get("token")
                if not token:
                    auth_header = request.headers.get("Authorization", "")
                    if auth_header.startswith("Bearer "):
                        token = auth_header[7:]
                
                if not token:
                    raise HTTPException(status_code=401, detail="Token required")
                
                # Use API name directly (FastAPI already decodes path parameters)
                decoded_api_name = api_name
                
                try:
                    # Find proxy connector by API name
                    proxy_connector = db.query(ProxyConnector).filter(
                        ProxyConnector.name == decoded_api_name,
                        ProxyConnector.connector_type == "api",
                        ProxyConnector.is_active == True
                    ).first()
                    
                    if not proxy_connector:
                        # Try case-insensitive search
                        proxy_connector = db.query(ProxyConnector).filter(
                            ProxyConnector.name.ilike(f"%{decoded_api_name}%"),
                            ProxyConnector.connector_type == "api",
                            ProxyConnector.is_active == True
                        ).first()
                    
                    if not proxy_connector:
                        # Try to find by share token
                        shared_link = db.query(SharedProxyLink).filter(
                            SharedProxyLink.share_id == token,
                            SharedProxyLink.is_active == True
                        ).first()
                        
                        if shared_link:
                            proxy_connector = shared_link.proxy_connector
                        else:
                            # Log available connectors for debugging
                            available_connectors = db.query(ProxyConnector).filter(
                                ProxyConnector.is_active == True
                            ).all()
                            connector_names = [c.name for c in available_connectors]
                            logger.error(f"API '{decoded_api_name}' not found. Available: {connector_names}")
                            raise HTTPException(status_code=404, detail=f"API '{decoded_api_name}' not found. Available: {connector_names}")
                    
                    # Handle API request
                    result = await self.handle_api_proxy(proxy_connector, request, db)
                    return result
                    
                except Exception as e:
                    logger.error(f"API proxy operation failed: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
        
        # Generic proxy endpoint for database access
        @app.get("/{database_name}")
        @app.post("/{database_name}")
        async def proxy_database_access(
            database_name: str,
            request: Request,
            token: Optional[str] = None,
            db: Session = Depends(get_db)
        ):
            """Handle database access through proxy"""
            
            # Get token from query params or headers
            if not token:
                token = request.query_params.get("token")
            if not token:
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:]
            
            if not token:
                raise HTTPException(status_code=401, detail="Token required")
            
            # Use database name directly (FastAPI already decodes path parameters)
            decoded_db_name = database_name
            
            try:
                # Find proxy connector by database name and type
                proxy_connector = db.query(ProxyConnector).filter(
                    ProxyConnector.name == decoded_db_name,
                    ProxyConnector.connector_type == "database",
                    ProxyConnector.is_active == True
                ).first()
                
                if not proxy_connector:
                    # Try to find by share token
                    shared_link = db.query(SharedProxyLink).filter(
                        SharedProxyLink.share_id == token,
                        SharedProxyLink.is_active == True
                    ).first()
                    
                    if shared_link:
                        proxy_connector = shared_link.proxy_connector
                    else:
                        raise HTTPException(status_code=404, detail="Database not found")
                
                # Execute database operation
                if request.method == "GET":
                    operation_data = {
                        "query": request.query_params.get("query", "SELECT 1"),
                        "operation": "select"
                    }
                else:
                    body = await request.json()
                    operation_data = body
                
                # Route to appropriate handler
                if proxy_type == "api":
                    result = await self.handle_api_proxy(proxy_connector, request, db)
                elif proxy_type == "mysql":
                    result = await self.handle_mysql_proxy(proxy_connector, operation_data, db)
                elif proxy_type == "postgresql":
                    result = await self.handle_postgresql_proxy(proxy_connector, operation_data, db)
                elif proxy_type == "clickhouse":
                    result = await self.handle_clickhouse_proxy(proxy_connector, operation_data, db)
                elif proxy_type == "mongodb":
                    result = await self.handle_mongodb_proxy(proxy_connector, operation_data, db)
                else:
                    raise HTTPException(status_code=400, detail=f"Unsupported proxy type: {proxy_type}")
                
                return result
                
            except Exception as e:
                logger.error(f"Proxy operation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Share link endpoint
        @app.get("/share/{share_id}")
        async def access_shared_link(
            share_id: str,
            request: Request,
            db: Session = Depends(get_db)
        ):
            """Access shared link through proxy"""
            
            try:
                shared_link = db.query(SharedProxyLink).filter(
                    SharedProxyLink.share_id == share_id,
                    SharedProxyLink.is_active == True
                ).first()
                
                if not shared_link:
                    raise HTTPException(status_code=404, detail="Shared link not found")
                
                # Check expiration
                if shared_link.expires_at and shared_link.expires_at < datetime.utcnow():
                    raise HTTPException(status_code=403, detail="Shared link expired")
                
                # Increment usage
                shared_link.current_uses += 1
                db.commit()
                
                return {
                    "message": "Shared link accessed",
                    "database_name": shared_link.proxy_connector.name,
                    "connection_info": {
                        "host": f"localhost:{port}",
                        "database": shared_link.proxy_connector.name,
                        "user": "proxy_user",
                        "password": share_id
                    }
                }
                
            except Exception as e:
                logger.error(f"Shared link access failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        return app
    
    async def handle_api_proxy(self, proxy_connector: ProxyConnector, request: Request, db: Session) -> Dict:
        """Handle API proxy operations"""
        
        try:
            # Get connection configuration
            logger.info(f"Processing API request for connector: {proxy_connector.name}")
            
            try:
                if isinstance(proxy_connector.real_connection_config, str):
                    # Try to decrypt or parse as JSON
                    try:
                        connection_config = json.loads(proxy_connector.real_connection_config)
                    except json.JSONDecodeError:
                        # Might be encrypted, try as simple string
                        connection_config = {"base_url": proxy_connector.real_connection_config}
                else:
                    connection_config = proxy_connector.real_connection_config
            except Exception as e:
                logger.error(f"Failed to parse connection config: {e}")
                # Fallback for JSONPlaceholder API
                connection_config = {"base_url": "https://jsonplaceholder.typicode.com"}
            
            # Get the external API URL
            external_url = connection_config.get('base_url') or connection_config.get('url')
            if not external_url:
                # Default to JSONPlaceholder for testing
                external_url = "https://jsonplaceholder.typicode.com"
                logger.warning(f"No API URL configured for {proxy_connector.name}, using default: {external_url}")
            
            # Prepare headers
            headers = {
                'User-Agent': 'AI-Share-Platform/1.0',
                'Accept': 'application/json'
            }
            
            # Add authentication if available
            try:
                if proxy_connector.real_credentials:
                    if isinstance(proxy_connector.real_credentials, str):
                        try:
                            credentials = json.loads(proxy_connector.real_credentials)
                        except json.JSONDecodeError:
                            credentials = {}
                    else:
                        credentials = proxy_connector.real_credentials
                    
                    api_key = credentials.get('api_key')
                    if api_key:
                        auth_header = credentials.get('auth_header', 'Authorization')
                        auth_prefix = credentials.get('auth_prefix', 'Bearer ')
                        headers[auth_header] = f"{auth_prefix}{api_key}"
            except Exception as e:
                logger.warning(f"Failed to parse credentials: {e}")
            
            # Build endpoint URL
            endpoint = request.query_params.get("endpoint", "/posts")  # Default to /posts for JSONPlaceholder
            full_url = f"{external_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            logger.info(f"Making API request to: {full_url}")
            
            # Make HTTP request to external API
            async with httpx.AsyncClient(timeout=30.0) as client:
                if request.method == "GET":
                    # Forward query parameters
                    params = dict(request.query_params)
                    # Remove internal parameters
                    params.pop('token', None)
                    params.pop('endpoint', None)
                    
                    response = await client.get(full_url, headers=headers, params=params)
                else:
                    # Forward POST body
                    body = await request.body()
                    response = await client.post(full_url, headers=headers, content=body)
            
            logger.info(f"API response status: {response.status_code}")
            logger.info(f"API response headers: {dict(response.headers)}")
            logger.info(f"API response content (first 200 chars): {response.text[:200]}")
            
            # Return response data with better error handling
            try:
                if response.headers.get('content-type', '').startswith('application/json'):
                    data = response.json()
                else:
                    data = response.text
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                data = response.text
            except Exception as e:
                logger.error(f"Response parsing error: {e}")
                data = response.text
            
            return {
                "status": "success",
                "data": data,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "raw_response": response.text[:500] if len(response.text) > 500 else response.text,
                "full_url": full_url
            }
            
        except httpx.TimeoutException:
            logger.error(f"API proxy timeout for {proxy_connector.name}")
            return {
                "status": "error",
                "error": "API request timeout"
            }
        except Exception as e:
            logger.error(f"API proxy operation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def handle_mysql_proxy(self, proxy_connector: ProxyConnector, operation_data: Dict, db: Session) -> Dict:
        """Handle MySQL proxy operations"""
        
        try:
            # Decrypt connection details
            real_config = json.loads(proxy_connector.real_connection_config)
            real_credentials = json.loads(proxy_connector.real_credentials)
            
            # Apply SSL configuration for development
            from app.core.config import settings
            
            host = real_config.get('host', 'localhost')
            port = real_config.get('port', 3306)
            
            # Get SSL-aware configuration
            ssl_config = settings.get_ssl_config_for_connector(
                'mysql', host, port, real_config
            )
            
            # Create MySQL connection
            config = {
                'host': host,
                'port': port,
                'user': real_credentials.get('username'),
                'password': real_credentials.get('password'),
                'database': real_config.get('database'),
                'connect_timeout': app_config.integrations.CONNECTOR_CONNECTION_TIMEOUT,
                'ssl_disabled': ssl_config.get('ssl_disabled', False)
            }
            
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor(dictionary=True)
            
            # Execute query
            query = operation_data.get('query', 'SELECT 1')
            cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
            else:
                results = []
                columns = []
                connection.commit()
            
            cursor.close()
            connection.close()
            
            return {
                "status": "success",
                "data": results,
                "columns": columns,
                "row_count": len(results)
            }
            
        except Exception as e:
            logger.error(f"MySQL proxy operation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def handle_postgresql_proxy(self, proxy_connector: ProxyConnector, operation_data: Dict, db: Session) -> Dict:
        """Handle PostgreSQL proxy operations"""
        
        try:
            # Decrypt connection details
            real_config = json.loads(proxy_connector.real_connection_config)
            real_credentials = json.loads(proxy_connector.real_credentials)
            
            # Apply SSL configuration for development
            from app.core.config import settings
            
            host = real_config.get('host', 'localhost')
            port = real_config.get('port', 5432)
            
            # Get SSL-aware configuration
            ssl_config = settings.get_ssl_config_for_connector(
                'postgresql', host, port, real_config
            )
            
            # Create PostgreSQL connection
            connection = psycopg2.connect(
                host=host,
                port=port,
                user=real_credentials.get('username'),
                password=real_credentials.get('password'),
                database=real_config.get('database'),
                sslmode=ssl_config.get('sslmode', 'prefer')
            )
            
            cursor = connection.cursor()
            
            # Execute query
            query = operation_data.get('query', 'SELECT 1')
            cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
            else:
                results = []
                columns = []
                connection.commit()
            
            cursor.close()
            connection.close()
            
            return {
                "status": "success",
                "data": results,
                "columns": columns,
                "row_count": len(results)
            }
            
        except Exception as e:
            logger.error(f"PostgreSQL proxy operation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def handle_clickhouse_proxy(self, proxy_connector: ProxyConnector, operation_data: Dict, db: Session) -> Dict:
        """Handle ClickHouse proxy operations"""
        
        try:
            # Decrypt connection details
            real_config = json.loads(proxy_connector.real_connection_config)
            real_credentials = json.loads(proxy_connector.real_credentials)
            
            # Create ClickHouse connection
            client = ClickHouseClient(
                host=real_config.get('host', 'localhost'),
                port=real_config.get('port', 9000),
                user=real_credentials.get('username'),
                password=real_credentials.get('password'),
                database=real_config.get('database')
            )
            
            # Execute query
            query = operation_data.get('query', 'SELECT 1')
            results = client.execute(query)
            
            return {
                "status": "success",
                "data": results,
                "row_count": len(results)
            }
            
        except Exception as e:
            logger.error(f"ClickHouse proxy operation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def handle_mongodb_proxy(self, proxy_connector: ProxyConnector, operation_data: Dict, db: Session) -> Dict:
        """Handle MongoDB proxy operations"""
        
        try:
            # Decrypt connection details
            real_config = json.loads(proxy_connector.real_connection_config)
            real_credentials = json.loads(proxy_connector.real_credentials)
            
            # Create MongoDB connection
            connection_string = f"mongodb://{real_credentials.get('username')}:{real_credentials.get('password')}@{real_config.get('host', 'localhost')}:{real_config.get('port', 27017)}/{real_config.get('database')}"
            
            client = pymongo.MongoClient(connection_string)
            db_conn = client[real_config.get('database')]
            
            # Execute operation
            collection_name = operation_data.get('collection', 'default')
            operation = operation_data.get('operation', 'find')
            query = operation_data.get('query', {})
            
            collection = db_conn[collection_name]
            
            if operation == 'find':
                results = list(collection.find(query))
            elif operation == 'insert':
                results = collection.insert_one(query)
            elif operation == 'update':
                results = collection.update_one(query.get('filter', {}), query.get('update', {}))
            else:
                results = []
            
            client.close()
            
            return {
                "status": "success",
                "data": results,
                "row_count": len(results) if isinstance(results, list) else 1
            }
            
        except Exception as e:
            logger.error(f"MongoDB proxy operation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def start_proxy_servers(self):
        """Start all proxy servers on their respective ports"""
        
        logger.info("🚀 Starting Multi-Port Proxy Service...")
        
        for proxy_type, port in PROXY_PORTS.items():
            try:
                app = self.create_proxy_app(proxy_type, port)
                self.apps[proxy_type] = app
                
                # Start server
                config = uvicorn.Config(
                    app=app,
                    host="0.0.0.0",
                    port=port,
                    log_level="info"
                )
                
                server = uvicorn.Server(config)
                self.servers[proxy_type] = server
                
                logger.info(f"✅ {proxy_type.upper()} proxy server starting on port {port}")
                
            except Exception as e:
                logger.error(f"❌ Failed to start {proxy_type} proxy server: {e}")
        
        # Start all servers concurrently
        tasks = []
        for proxy_type, server in self.servers.items():
            task = asyncio.create_task(server.serve())
            tasks.append(task)
            logger.info(f"🌐 {proxy_type.upper()} proxy server running on http://localhost:{PROXY_PORTS[proxy_type]}")
        
        logger.info("🎉 All proxy servers started successfully!")
        logger.info("Port allocation:")
        for proxy_type, port in PROXY_PORTS.items():
            logger.info(f"  - {proxy_type.upper()}: http://localhost:{port}")
        
        # Wait for all servers
        await asyncio.gather(*tasks)

# Main execution
if __name__ == "__main__":
    proxy_service = MultiPortProxyService()
    
    try:
        asyncio.run(proxy_service.start_proxy_servers())
    except KeyboardInterrupt:
        logger.info("🛑 Proxy service stopped by user")
    except Exception as e:
        logger.error(f"❌ Proxy service failed: {e}")