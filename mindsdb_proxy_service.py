"""
MindsDB-based Multi-Port Proxy Service
Creates dedicated ports for different database types using MindsDB connectors
"""

import asyncio
import logging
import json
import urllib.parse
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Query, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx
from sqlalchemy.orm import Session
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import get_db
from app.services.mindsdb import MindsDBService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Port configuration for different proxy types - all ports above 10100
PROXY_PORTS = {
    'mysql': 10101,      # High port for MySQL proxy
    'postgresql': 10102, # High port for PostgreSQL proxy  
    'api': 10103,        # High port for API connections
    'clickhouse': 10104, # High port for ClickHouse proxy
    'mongodb': 10105,    # High port for MongoDB proxy
    's3': 10106,         # High port for S3 proxy
    'shared_link': 10107 # High port for shared links
}

class MindsDBProxyService:
    """MindsDB-based proxy service with dedicated ports"""
    
    def __init__(self):
        self.mindsdb_service = MindsDBService()
        self.apps = {}
        self.servers = {}
        
        # Test databases configuration
        self.test_databases = {
            "Test DB Unipa Dataset": {
                "type": "mysql",
                "config": {
                    "host": "localhost",
                    "port": 3306,
                    "database": "test_db",
                    "user": "test_user",
                    "password": "test_password"
                },
                "token": "0627b5b4afdba49bb348a870eb152e86"
            },
            "API Demo 1 Dataset": {
                "type": "api",
                "config": {
                    "base_url": "https://api.example.com",
                    "api_key": "demo_api_key",
                    "endpoint": "/data"
                },
                "token": "2c453b14d69ae40e61fdf190583dc588"
            }
        }
        
    def create_proxy_app(self, proxy_type: str, port: int) -> FastAPI:
        """Create a FastAPI app for a specific proxy type"""
        
        app = FastAPI(
            title=f"{proxy_type.upper()} Proxy Service",
            description=f"MindsDB-based proxy service for {proxy_type} connections",
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
            """Health check endpoint"""
            return {
                "status": "healthy",
                "proxy_type": proxy_type,
                "port": port,
                "mindsdb_status": await self.check_mindsdb_status(),
                "timestamp": datetime.now().isoformat()
            }
        
        @app.get("/")
        async def root():
            """Root endpoint"""
            return {
                "message": f"{proxy_type.upper()} Proxy Service",
                "proxy_type": proxy_type,
                "port": port,
                "available_databases": list(self.test_databases.keys()),
                "endpoints": [
                    f"/{proxy_type}/<database_name>",
                    f"/share/<share_id>",
                    "/health"
                ]
            }
        
        @app.get("/{database_name}")
        async def proxy_database_get(
            database_name: str,
            request: Request,
            token: Optional[str] = Query(None),
            query: Optional[str] = Query("SELECT 1 as test"),
            db: Session = Depends(get_db)
        ):
            """Handle database GET requests through MindsDB proxy"""
            return await self.handle_database_request(
                database_name, request, token, query, proxy_type, db
            )
        
        @app.post("/{database_name}")
        async def proxy_database_post(
            database_name: str,
            request: Request,
            token: Optional[str] = Query(None),
            db: Session = Depends(get_db)
        ):
            """Handle database POST requests through MindsDB proxy"""
            try:
                body = await request.json()
                query = body.get("query", "SELECT 1 as test")
            except:
                query = "SELECT 1 as test"
            
            return await self.handle_database_request(
                database_name, request, token, query, proxy_type, db
            )
        
        @app.get("/share/{share_id}")
        async def access_shared_link(
            share_id: str,
            request: Request,
            db: Session = Depends(get_db)
        ):
            """Access shared link through proxy"""
            return await self.handle_shared_link_access(share_id, proxy_type, port, db)
        
        return app
    
    async def handle_database_request(
        self,
        database_name: str,
        request: Request,
        token: Optional[str],
        query: Optional[str],
        proxy_type: str,
        db: Session
    ) -> Dict[str, Any]:
        """Handle database requests through MindsDB"""
        
        # Decode database name
        decoded_db_name = urllib.parse.unquote(database_name)
        
        # Get token from various sources
        if not token:
            token = request.query_params.get("token")
        if not token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
        
        logger.info(f"Database request: {decoded_db_name}, Token: {token}, Type: {proxy_type}")
        
        # Check if database exists
        if decoded_db_name not in self.test_databases:
            raise HTTPException(
                status_code=404,
                detail=f"Database '{decoded_db_name}' not found. Available: {list(self.test_databases.keys())}"
            )
        
        db_config = self.test_databases[decoded_db_name]
        
        # Validate token
        if token != db_config["token"]:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
        
        # Check if proxy type matches database type
        if proxy_type != db_config["type"]:
            raise HTTPException(
                status_code=400,
                detail=f"Proxy type '{proxy_type}' doesn't match database type '{db_config['type']}'"
            )
        
        try:
            # Create MindsDB connection
            connection_name = f"{decoded_db_name.replace(' ', '_').lower()}_conn"
            
            # Create database connection in MindsDB
            await self.create_mindsdb_connection(connection_name, db_config)
            
            # Execute query through MindsDB
            result = await self.execute_mindsdb_query(connection_name, query or "SELECT 1 as test")
            
            return {
                "status": "success",
                "database": decoded_db_name,
                "proxy_type": proxy_type,
                "query": query,
                "data": result.get("data", []),
                "columns": result.get("columns", []),
                "row_count": len(result.get("data", [])),
                "connection_info": {
                    "proxy_host": f"localhost:{PROXY_PORTS[proxy_type]}",
                    "database": decoded_db_name,
                    "user": "proxy_user",
                    "mindsdb_connection": connection_name
                }
            }
            
        except Exception as e:
            logger.error(f"Database request failed: {e}")
            return {
                "status": "error",
                "database": decoded_db_name,
                "proxy_type": proxy_type,
                "error": str(e),
                "query": query
            }
    
    async def handle_shared_link_access(
        self,
        share_id: str,
        proxy_type: str,
        port: int,
        db: Session
    ) -> Dict[str, Any]:
        """Handle shared link access"""
        
        # Find database by token
        for db_name, db_config in self.test_databases.items():
            if db_config["token"] == share_id:
                return {
                    "status": "success",
                    "message": "Shared link accessed",
                    "database_name": db_name,
                    "proxy_type": proxy_type,
                    "connection_info": {
                        "host": f"localhost:{port}",
                        "database": db_name,
                        "user": "proxy_user",
                        "password": share_id
                    },
                    "usage": f"Access via: http://localhost:{port}/{urllib.parse.quote(db_name)}?token={share_id}"
                }
        
        raise HTTPException(
            status_code=404,
            detail="Shared link not found"
        )
    
    async def create_mindsdb_connection(self, connection_name: str, db_config: Dict[str, Any]):
        """Create a database connection in MindsDB"""
        
        try:
            db_type = db_config["type"]
            config = db_config["config"]
            
            # Create connection SQL based on database type
            if db_type == "mysql":
                connection_sql = f"""
                CREATE DATABASE {connection_name}
                WITH ENGINE = 'mysql',
                PARAMETERS = {{
                    "host": "{config['host']}",
                    "port": {config['port']},
                    "database": "{config['database']}",
                    "user": "{config['user']}",
                    "password": "{config['password']}"
                }};
                """
            elif db_type == "postgresql":
                connection_sql = f"""
                CREATE DATABASE {connection_name}
                WITH ENGINE = 'postgres',
                PARAMETERS = {{
                    "host": "{config['host']}",
                    "port": {config['port']},
                    "database": "{config['database']}",
                    "user": "{config['user']}",
                    "password": "{config['password']}"
                }};
                """
            elif db_type == "clickhouse":
                connection_sql = f"""
                CREATE DATABASE {connection_name}
                WITH ENGINE = 'clickhouse',
                PARAMETERS = {{
                    "host": "{config['host']}",
                    "port": {config['port']},
                    "database": "{config['database']}",
                    "user": "{config['user']}",
                    "password": "{config['password']}"
                }};
                """
            elif db_type == "mongodb":
                connection_sql = f"""
                CREATE DATABASE {connection_name}
                WITH ENGINE = 'mongodb',
                PARAMETERS = {{
                    "host": "{config['host']}",
                    "port": {config['port']},
                    "database": "{config['database']}",
                    "user": "{config['user']}",
                    "password": "{config['password']}"
                }};
                """
            elif db_type == "api":
                connection_sql = f"""
                CREATE DATABASE {connection_name}
                WITH ENGINE = 'rest_api',
                PARAMETERS = {{
                    "base_url": "{config['base_url']}",
                    "api_key": "{config['api_key']}",
                    "endpoint": "{config['endpoint']}"
                }};
                """
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            # Execute connection creation (for now, just log it)
            logger.info(f"Creating MindsDB connection: {connection_name}")
            logger.info(f"SQL: {connection_sql}")
            
            # In a real implementation, you would execute this SQL in MindsDB
            # For now, we'll simulate success
            return True
            
        except Exception as e:
            logger.error(f"Failed to create MindsDB connection: {e}")
            raise
    
    async def execute_mindsdb_query(self, connection_name: str, query: str) -> Dict[str, Any]:
        """Execute a query through MindsDB"""
        
        try:
            # For now, return mock data
            # In a real implementation, you would execute: SELECT * FROM {connection_name}.{table_name}
            
            logger.info(f"Executing query on {connection_name}: {query}")
            
            # Mock response
            if "SELECT" in query.upper():
                return {
                    "data": [
                        {"id": 1, "name": "MindsDB Record 1", "value": 100},
                        {"id": 2, "name": "MindsDB Record 2", "value": 200},
                        {"id": 3, "name": "MindsDB Record 3", "value": 300}
                    ],
                    "columns": ["id", "name", "value"]
                }
            else:
                return {
                    "data": [],
                    "columns": [],
                    "message": "Query executed successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to execute MindsDB query: {e}")
            raise
    
    async def check_mindsdb_status(self) -> str:
        """Check MindsDB service status"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:47334/api/status", timeout=5)
                if response.status_code == 200:
                    return "available"
                else:
                    return "unavailable"
        except:
            return "unavailable"
    
    async def start_proxy_servers(self):
        """Start all proxy servers on their respective ports"""
        
        logger.info("🚀 Starting MindsDB Multi-Port Proxy Service...")
        
        # Check MindsDB status
        mindsdb_status = await self.check_mindsdb_status()
        logger.info(f"MindsDB Status: {mindsdb_status}")
        
        tasks = []
        
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
                
                # Create task for this server
                task = asyncio.create_task(server.serve())
                tasks.append(task)
                
                logger.info(f"✅ {proxy_type.upper()} proxy server starting on port {port}")
                
            except Exception as e:
                logger.error(f"❌ Failed to start {proxy_type} proxy server: {e}")
        
        logger.info("🎉 All proxy servers started successfully!")
        logger.info("Port allocation:")
        for proxy_type, port in PROXY_PORTS.items():
            logger.info(f"  - {proxy_type.upper()}: http://localhost:{port}")
        
        logger.info("📋 Test database available:")
        for db_name, db_config in self.test_databases.items():
            logger.info(f"  - {db_name} ({db_config['type']}): token={db_config['token']}")
        
        # Wait for all servers
        await asyncio.gather(*tasks)

# Main execution
if __name__ == "__main__":
    proxy_service = MindsDBProxyService()
    
    try:
        asyncio.run(proxy_service.start_proxy_servers())
    except KeyboardInterrupt:
        logger.info("🛑 Proxy service stopped by user")
    except Exception as e:
        logger.error(f"❌ Proxy service failed: {e}")
        import traceback
        traceback.print_exc()