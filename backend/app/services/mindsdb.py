import requests
from typing import Dict, List, Optional, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class MindsDBService:
    def __init__(self):
        self.base_url = settings.MINDSDB_URL
        self.database = settings.MINDSDB_DATABASE
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to MindsDB API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"MindsDB request failed: {e}")
            raise Exception(f"MindsDB request failed: {e}")
    
    def execute_sql(self, query: str) -> Dict[str, Any]:
        """Execute SQL query on MindsDB."""
        endpoint = "/api/sql/query"
        payload = {"query": query}
        return self._make_request("POST", endpoint, json=payload)
    
    def create_model(self, model_name: str, query: str, engine: str = "openai") -> Dict[str, Any]:
        """Create a new ML model in MindsDB."""
        sql_query = f"""
        CREATE MODEL {model_name}
        PREDICT target_column
        USING
            engine = '{engine}',
            {query}
        """
        return self.execute_sql(sql_query)
    
    def get_models(self) -> List[Dict[str, Any]]:
        """Get list of all models."""
        query = "SHOW MODELS;"
        result = self.execute_sql(query)
        return result.get("data", [])
    
    def predict(self, model_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction using a model."""
        # Convert data to WHERE clause
        where_conditions = []
        for key, value in data.items():
            if isinstance(value, str):
                where_conditions.append(f"{key} = '{value}'")
            else:
                where_conditions.append(f"{key} = {value}")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"SELECT * FROM {model_name} WHERE {where_clause};"
        return self.execute_sql(query)
    
    def delete_model(self, model_name: str) -> Dict[str, Any]:
        """Delete a model."""
        query = f"DROP MODEL {model_name};"
        return self.execute_sql(query)
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        query = f"DESCRIBE {model_name};"
        return self.execute_sql(query)
    
    def create_database_connection(self, db_name: str, engine: str, connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a database connection."""
        # Convert connection params to WITH clause
        with_params = []
        for key, value in connection_params.items():
            if isinstance(value, str):
                with_params.append(f"{key} = '{value}'")
            else:
                with_params.append(f"{key} = {value}")
        
        with_clause = ", ".join(with_params)
        
        query = f"""
        CREATE DATABASE {db_name}
        WITH ENGINE = '{engine}',
        PARAMETERS = {{{with_clause}}};
        """
        return self.execute_sql(query)
    
    def get_databases(self) -> List[Dict[str, Any]]:
        """Get list of all database connections."""
        query = "SHOW DATABASES;"
        result = self.execute_sql(query)
        return result.get("data", [])
    
    def test_connection(self) -> bool:
        """Test connection to MindsDB."""
        try:
            endpoint = "/api/status"
            response = self._make_request("GET", endpoint)
            return response.get("status") == "ok"
        except Exception:
            return False


# Global instance
mindsdb_service = MindsDBService() 