import mindsdb_sdk
import google.generativeai as genai
from typing import Dict, List, Optional, Any
from app.core.config import settings
from app.core.app_config import get_app_config
import logging
import json
import os
from datetime import datetime
import time
import requests

# Import for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.file_handler import FileUpload

logger = logging.getLogger(__name__)


class MindsDBService:
    def __init__(self):
        # Get centralized configuration
        self.app_config = get_app_config()
        
        # Use settings from centralized configuration
        self.base_url = self.app_config.services.get_mindsdb_url()
        self.api_key = self.app_config.integrations.GOOGLE_API_KEY
        
        # Debug log the API key (masked for security)
        if self.api_key:
            masked_key = self.api_key[:4] + "..." + self.api_key[-4:] if len(self.api_key) > 8 else "***"
            logger.info(f"✅ Google API key loaded: {masked_key}")
        else:
            logger.warning("⚠️ No Google API key found in settings")
            # Try to load directly from environment
            import os
            self.api_key = os.environ.get("GOOGLE_API_KEY")
            if self.api_key:
                masked_key = self.api_key[:4] + "..." + self.api_key[-4:] if len(self.api_key) > 8 else "***"
                logger.info(f"✅ Google API key loaded from environment: {masked_key}")
            else:
                logger.error("❌ No Google API key found in environment either")
        
        # Model configurations from environment
        self.engine_name = settings.GEMINI_ENGINE_NAME
        self.default_model = settings.DEFAULT_GEMINI_MODEL
        self.chat_model_name = settings.GEMINI_CHAT_MODEL_NAME
        self.vision_model_name = settings.GEMINI_VISION_MODEL_NAME
        self.embedding_model_name = settings.GEMINI_EMBEDDING_MODEL_NAME
        
        # Configure Gemini directly as backup
        genai.configure(api_key=self.api_key)
        
        # Connection state
        self.connection = None
        self._connected = False

    def _ensure_connection(self) -> bool:
        """Ensure MindsDB SDK connection is established."""
        if self._connected and self.connection:
            return True
            
        try:
            logger.info(f"🔗 Connecting to MindsDB SDK at {self.base_url}")
            self.connection = mindsdb_sdk.connect(self.base_url)
            
            # Ensure we're using the mindsdb project
            try:
                self.connection.query("USE mindsdb")
                logger.info(f"✅ Using mindsdb project")
            except Exception as e:
                logger.warning(f"⚠️ Could not set mindsdb project: {e}")
            
            self._connected = True
            logger.info(f"✅ Connected to MindsDB SDK at {self.base_url}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MindsDB: {e}")
            self._connected = False
            return False

    def health_check(self) -> Dict[str, Any]:
        """Perform health check of MindsDB service."""
        try:
            if not self._ensure_connection():
                return {"status": "error", "connection": "failed"}

            # Try to execute a simple query to test connection
            try:
                # Use raw SQL query instead of SDK methods
                result = self.connection.query("SELECT 1 as test")
                df = result.fetch()
                
                if not df.empty:
                    logger.info("🏥 Health check completed successfully")
                    return {
                        "status": "healthy",
                        "connection": "connected",
                        "engine_status": "accessible",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    raise Exception("Empty result from health check query")
                
            except Exception as e:
                logger.warning(f"Health check query failed: {e}")
                return {
                    "status": "partial",
                    "connection": "connected",
                    "engine_status": "unknown",
                    "warning": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {
                "status": "error",
                "connection": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a SQL query on MindsDB and return results"""
        try:
            if not self._ensure_connection():
                return {"status": "error", "error": "MindsDB connection not available"}

            logger.info(f"🔍 Executing query: {query}")
            
            result = self.connection.query(query)
            
            if result and hasattr(result, 'fetch'):
                df = result.fetch()
                # Handle case where fetch() returns None
                if df is not None and hasattr(df, 'empty'):
                    return {
                        "status": "success",
                        "rows": df.to_dict('records') if not df.empty else [],
                        "columns": list(df.columns) if not df.empty else [],
                        "row_count": len(df)
                    }
                else:
                    # For DDL queries (CREATE, DROP, etc.) that don't return data
                    logger.info("✅ Query executed successfully (no data returned)")
                    return {
                        "status": "success",
                        "rows": [],
                        "columns": [],
                        "row_count": 0,
                        "message": "Query executed successfully"
                    }
            else:
                # For queries that don't have fetch method or return None
                logger.info("✅ Query executed successfully (no result object)")
                return {
                    "status": "success",
                    "rows": [],
                    "columns": [],
                    "row_count": 0,
                    "message": "Query executed successfully"
                }
                
        except Exception as e:
            logger.error(f"❌ Query execution failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def create_gemini_engine(self) -> Dict[str, Any]:
        """Create or verify Google Gemini engine using raw SQL."""
        try:
            if not self._ensure_connection():
                return {"message": "SDK connection not available", "status": "error"}

            # Check if engine already exists first
            try:
                engines_query = "SHOW ML_ENGINES"
                result = self.connection.query(engines_query)
                engines_df = result.fetch()
                
                if not engines_df.empty:
                    for _, engine in engines_df.iterrows():
                        if engine.get('NAME') == self.engine_name:
                            logger.info(f"✅ Engine {self.engine_name} already exists")
                            return {
                                "message": f"Engine {self.engine_name} ready",
                                "status": "exists",
                                "engine_name": self.engine_name
                            }
            except Exception as e:
                logger.warning(f"⚠️ Could not check existing engines: {e}")

            # Try to use OpenAI as fallback since Gemini engine creation seems to have issues
            logger.warning(f"⚠️ Gemini engine creation having issues, trying OpenAI as fallback")
            
            # Check if we have OpenAI API key as fallback
            openai_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not openai_key:
                import os
                openai_key = os.environ.get('OPENAI_API_KEY')
            
            if openai_key:
                # Try creating OpenAI engine as fallback
                openai_engine_name = "openai_engine_fallback"
                create_openai_engine_sql = f"""
                CREATE ML_ENGINE {openai_engine_name}
                FROM openai
                USING
                    api_key = '{openai_key}';
                """
                
                try:
                    logger.info(f"🔧 Creating OpenAI fallback engine: {openai_engine_name}")
                    self.connection.query(create_openai_engine_sql)
                    
                    # Wait and verify
                    import time
                    time.sleep(3)
                    
                    result = self.connection.query("SHOW ML_ENGINES")
                    engines_df = result.fetch()
                    
                    for _, engine in engines_df.iterrows():
                        if engine.get('NAME') == openai_engine_name:
                            logger.info(f"✅ OpenAI fallback engine created successfully")
                            # Update the engine name for this session
                            self.engine_name = openai_engine_name
                            return {
                                "message": f"OpenAI fallback engine {openai_engine_name} created",
                                "status": "created",
                                "engine_name": openai_engine_name
                            }
                            
                except Exception as openai_error:
                    logger.warning(f"⚠️ OpenAI fallback also failed: {openai_error}")
            
            # If all else fails, try the original Gemini approach one more time
            logger.info(f"🔧 Attempting Gemini engine creation one more time")
            create_engine_sql = f"""
            CREATE ML_ENGINE {self.engine_name}
            FROM google_gemini
            USING
                api_key = '{self.api_key}';
            """
            
            try:
                logger.info(f"🔧 Creating engine with SQL: {create_engine_sql}")
                self.connection.query(create_engine_sql)
                
                # Just return success even if we can't verify it
                # The model creation will test if it actually works
                logger.info(f"✅ Engine creation command executed")
                return {
                    "message": f"Engine {self.engine_name} creation attempted",
                    "status": "created",
                    "engine_name": self.engine_name
                }
                    
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"✅ Engine {self.engine_name} already exists")
                    return {
                        "message": f"Engine {self.engine_name} ready",
                        "status": "exists",
                        "engine_name": self.engine_name
                    }
                else:
                    raise e
                    
        except Exception as e:
            logger.error(f"❌ Failed to create/verify engine {self.engine_name}: {e}")
            return {
                "message": f"Engine creation failed: {str(e)}",
                "status": "error",
                "engine_name": self.engine_name
            }

    def create_gemini_model(
        self, 
        model_name: str, 
        model_type: str = "chat",
        column_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a Gemini model using raw SQL."""
        try:
            if not self._ensure_connection():
                return {"message": "SDK connection not available", "status": "error"}

            # Ensure engine exists first
            engine_result = self.create_gemini_engine()
            if engine_result.get("status") == "error":
                return {"message": "Engine creation failed", "status": "error"}

            # Check if model already exists
            try:
                models_query = "SHOW MODELS"
                result = self.connection.query(models_query)
                models_df = result.fetch()
                
                if not models_df.empty:
                    for _, model in models_df.iterrows():
                        if model.get('NAME') == model_name:
                            model_status = model.get('STATUS', 'Unknown')
                            logger.info(f"✅ Model {model_name} already exists (Status: {model_status})")
                            return {
                                "message": f"Model {model_name} ready",
                                "status": "exists",
                                "model_name": model_name
                            }
            except Exception as e:
                logger.warning(f"⚠️ Could not check existing models: {e}")

            # Set default column name
            if not column_name:
                column_name = "question"

            # Determine which engine to use and appropriate model syntax
            engine_name = self.engine_name
            model_sql = ""
            
            if "openai" in engine_name.lower():
                # OpenAI model syntax
                model_sql = f"""
                CREATE MODEL {model_name}
                PREDICT response
                USING
                    engine = '{engine_name}',
                    model_name = 'gpt-3.5-turbo',
                    prompt_template = 'Answer the following question: {{{{question}}}}';
                """
            else:
                # Gemini model syntax
                model_sql = f"""
                CREATE MODEL {model_name}
                PREDICT response
                USING
                    engine = '{engine_name}',
                    model_name = '{self.default_model}',
                    prompt_template = 'Answer the following question: {{{{question}}}}';
                """
            
            try:
                logger.info(f"🤖 Creating model with SQL: {model_sql}")
                self.connection.query(model_sql)
                
                # Wait for model to initialize
                import time
                logger.info(f"⏳ Waiting for model {model_name} to initialize...")
                time.sleep(8)  # Increased wait time
                
                # Verify model was created and check its status
                result = self.connection.query("SHOW MODELS")
                models_df = result.fetch()
                
                model_found = False
                model_status = "Unknown"
                if not models_df.empty:
                    for _, model in models_df.iterrows():
                        if model.get('NAME') == model_name:
                            model_found = True
                            model_status = model.get('STATUS', 'Unknown')
                            logger.info(f"✅ Model {model_name} found with status: {model_status}")
                            break
                
                if model_found:
                    return {
                        "message": f"Model {model_name} created successfully (Status: {model_status})",
                        "status": "created",
                        "model_name": model_name,
                        "engine": engine_name,
                        "column": column_name,
                        "model": self.default_model,
                        "model_status": model_status
                    }
                else:
                    # Even if we can't find it in SHOW MODELS, return success
                    # The actual chat test will determine if it works
                    logger.warning(f"⚠️ Model {model_name} not found in SHOW MODELS but creation command succeeded")
                    return {
                        "message": f"Model {model_name} creation attempted",
                        "status": "created",
                        "model_name": model_name,
                        "engine": engine_name,
                        "column": column_name,
                        "model": self.default_model,
                        "model_status": "unknown"
                    }
                
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"✅ Model {model_name} already exists")
                    return {
                        "message": f"Model {model_name} ready",
                        "status": "exists",
                        "model_name": model_name
                    }
                else:
                    raise e
            
        except Exception as e:
            logger.error(f"❌ Failed to create model {model_name}: {e}")
            return {
                "message": f"Model creation failed: {str(e)}",
                "status": "error",
                "model_name": model_name
            }

    def ai_chat(self, message: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Handle AI chat using direct Google Gemini API as fallback when MindsDB models fail."""
        if not model_name:
            model_name = self.chat_model_name

        try:
            # First try MindsDB approach
            if self._ensure_connection() and self.connection:
                try:
                    logger.info(f"💬 Attempting MindsDB chat with model: {model_name}")
                    
                    # First ensure the model exists and is ready
                    model_result = self.create_gemini_model(model_name)
                    if model_result.get("status") == "error":
                        logger.warning(f"⚠️ MindsDB model creation failed: {model_result.get('message')}")
                        raise Exception(f"Model creation failed: {model_result.get('message')}")
                    
                    # Wait a moment for the model to be ready
                    import time
                    time.sleep(2)
                    
                    # Query the model using MindsDB
                    query = f"""
                    SELECT response 
                    FROM {model_name} 
                    WHERE question = '{message.replace("'", "''")}'
                    """
                    
                    logger.info(f"🔍 Executing MindsDB query: {query}")
                    result = self.connection.query(query)
                    
                    if result:
                        try:
                            if hasattr(result, 'fetch'):
                                rows = result.fetch()
                                if hasattr(rows, 'empty') and not rows.empty:
                                    rows = rows.to_dict('records')
                                elif not isinstance(rows, list):
                                    rows = [rows] if rows is not None else []
                            else:
                                rows = []
                            
                            if rows and len(rows) > 0:
                                row_data = rows[0]
                                answer = ""
                                
                                if isinstance(row_data, dict):
                                    answer = row_data.get('response', '')
                                else:
                                    answer = str(row_data)
                                
                                if not isinstance(answer, str):
                                    answer = str(answer)
                                
                                # Clean up the response format
                                if answer.startswith("{0: '") and answer.endswith("'}"):
                                    answer = answer[5:-2]
                                elif answer.startswith("{0: \"") and answer.endswith("\"}"):
                                    answer = answer[5:-2]
                                
                                answer = answer.replace('\\n', '\n').strip()
                                
                                if answer and answer.strip():
                                    logger.info(f"✅ MindsDB chat successful")
                                    return {
                                        "answer": answer,
                                        "model": f"{model_name} (MindsDB)",
                                        "timestamp": datetime.utcnow().isoformat(),
                                        "tokens_used": len(message.split()) + len(answer.split()),
                                        "source": "mindsdb"
                                    }
                                else:
                                    logger.warning(f"⚠️ MindsDB returned empty response")
                                    raise Exception("Empty response from MindsDB")
                            else:
                                logger.warning(f"⚠️ MindsDB returned no rows")
                                raise Exception("No rows returned from MindsDB")
                                
                        except Exception as fetch_error:
                            logger.warning(f"⚠️ MindsDB fetch error: {fetch_error}")
                            raise Exception(f"MindsDB fetch failed: {fetch_error}")
                
                except Exception as mindsdb_error:
                    logger.warning(f"⚠️ MindsDB chat failed: {mindsdb_error}")
                    # Fall through to direct API approach
            
            # Fallback to direct Google Gemini API
            logger.info(f"🔄 Using direct Google Gemini API as fallback")
            
            if not self.api_key:
                raise Exception("No Google API key available for direct API access")
            
            import google.generativeai as genai
            
            # Configure Gemini API
            genai.configure(api_key=self.api_key)
            
            # Use a stable model
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Generate response
            response = model.generate_content(message)
            
            if response and response.text:
                logger.info(f"✅ Direct Google API chat successful")
                return {
                    "answer": response.text.strip(),
                    "model": "gemini-1.5-flash (Direct API)",
                    "timestamp": datetime.utcnow().isoformat(),
                    "tokens_used": len(message.split()) + len(response.text.split()),
                    "source": "google_direct_api"
                }
            else:
                raise Exception("No response from Google API")

        except Exception as e:
            logger.error(f"❌ AI chat failed completely: {e}")
            return {
                "answer": f"I'm sorry, but I encountered an error while processing your question: {str(e)}",
                "error": f"Chat failed: {str(e)}",
                "model": "Error Handler",
                "timestamp": datetime.utcnow().isoformat(),
                "source": "error"
            }

    def create_dataset_connection(self, dataset_name: str, file_url: str, file_type: str = "csv") -> Dict[str, Any]:
        """Create a dataset connection in MindsDB using a file URL."""
        try:
            if not self._ensure_connection():
                return {"status": "error", "message": "MindsDB connection not available"}

            # Sanitize dataset name for SQL
            safe_dataset_name = dataset_name.replace(" ", "_").replace("-", "_")
            safe_dataset_name = "".join(c for c in safe_dataset_name if c.isalnum() or c == "_")
            
            logger.info(f"🔗 Creating dataset connection: {safe_dataset_name} from {file_url}")
            
            # Create dataset from URL
            if file_type.lower() in ["csv", "json"]:
                create_query = f"""
                CREATE OR REPLACE DATASOURCE {safe_dataset_name}_datasource (
                    url '{file_url}',
                    type '{file_type.lower()}'
                )
                """
            else:
                # For other file types, create a generic datasource
                create_query = f"""
                CREATE OR REPLACE DATASOURCE {safe_dataset_name}_datasource (
                    url '{file_url}'
                )
                """
            
            logger.info(f"🔍 Executing dataset creation query: {create_query}")
            result = self.connection.query(create_query)
            
            return {
                "status": "success",
                "message": f"Dataset connection created: {safe_dataset_name}_datasource",
                "dataset_name": safe_dataset_name,
                "datasource_name": f"{safe_dataset_name}_datasource",
                "file_url": file_url
            }
            
        except Exception as e:
            logger.error(f"❌ Dataset connection creation failed: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to create dataset connection: {str(e)}"
            }

    def query_dataset(self, dataset_name: str, query: str) -> Dict[str, Any]:
        """Execute a query against a dataset in MindsDB."""
        try:
            if not self._ensure_connection():
                return {"status": "error", "message": "MindsDB connection not available"}

            safe_dataset_name = dataset_name.replace(" ", "_").replace("-", "_")
            safe_dataset_name = "".join(c for c in safe_dataset_name if c.isalnum() or c == "_")
            
            # Replace dataset placeholders in query
            formatted_query = query.replace("{dataset}", f"{safe_dataset_name}_datasource")
            
            logger.info(f"🔍 Executing dataset query: {formatted_query}")
            result = self.connection.query(formatted_query)
            
            if result and hasattr(result, 'fetch'):
                df = result.fetch()
                if df is not None and hasattr(df, 'empty'):
                    return {
                        "status": "success",
                        "rows": df.to_dict('records') if not df.empty else [],
                        "columns": list(df.columns) if not df.empty else [],
                        "row_count": len(df)
                    }
            
            return {
                "status": "success",
                "message": "Query executed successfully",
                "rows": [],
                "columns": [],
                "row_count": 0
            }
            
        except Exception as e:
            logger.error(f"❌ Dataset query failed: {str(e)}")
            return {
                "status": "error",
                "message": f"Query failed: {str(e)}"
            }

    def create_web_connector(
        self, 
        connector_name: str, 
        base_url: str, 
        endpoint: str = "",
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        auth_config: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a MindsDB web connector for API endpoints."""
        try:
            if not self._ensure_connection():
                return {"success": False, "error": "MindsDB connection not available"}

            # Clean connector name for MindsDB
            clean_name = connector_name.lower().replace(' ', '_').replace('-', '_')
            
            # Build the full URL
            full_url = f"{base_url.rstrip('/')}{endpoint}"
            
            # Prepare connection parameters
            connection_params = {
                "url": full_url,
                "method": method.upper()
            }
            
            # Add headers if provided
            if headers:
                connection_params["headers"] = headers
            
            # Add authentication if provided
            if auth_config:
                if auth_config.get("api_key"):
                    if auth_config.get("auth_header"):
                        connection_params["headers"] = connection_params.get("headers", {})
                        connection_params["headers"][auth_config["auth_header"]] = auth_config["api_key"]
                    else:
                        connection_params["headers"] = connection_params.get("headers", {})
                        connection_params["headers"]["Authorization"] = f"Bearer {auth_config['api_key']}"

            # Create the web connector using MindsDB SQL
            create_connector_sql = f"""
            CREATE DATABASE IF NOT EXISTS {clean_name}
            WITH ENGINE = 'web',
            PARAMETERS = {json.dumps(connection_params)};
            """
            
            logger.info(f"🔗 Creating web connector: {clean_name}")
            logger.info(f"📄 SQL: {create_connector_sql}")
            
            try:
                result = self.connection.query(create_connector_sql)
                logger.info(f"✅ Web connector {clean_name} created successfully")
                
                # Test the connector by trying to fetch data
                test_result = self.test_web_connector(clean_name)
                
                return {
                    "success": True,
                    "connector_name": clean_name,
                    "database_name": clean_name,
                    "url": full_url,
                    "method": method,
                    "test_result": test_result,
                    "message": f"Web connector {clean_name} created successfully"
                }
                
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"✅ Web connector {clean_name} already exists")
                    return {
                        "success": True,
                        "connector_name": clean_name,
                        "database_name": clean_name,
                        "url": full_url,
                        "method": method,
                        "message": f"Web connector {clean_name} already exists"
                    }
                else:
                    raise e
                    
        except Exception as e:
            logger.error(f"❌ Failed to create web connector {connector_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "connector_name": connector_name
            }

    def test_web_connector(self, connector_name: str) -> Dict[str, Any]:
        """Test a web connector by fetching sample data."""
        try:
            if not self._ensure_connection():
                return {"success": False, "error": "MindsDB connection not available"}

            # For web connectors, first check what tables are available
            try:
                show_tables_query = f"SHOW TABLES FROM {connector_name}"
                logger.info(f"🔍 Checking available tables: {show_tables_query}")
                tables_result = self.connection.query(show_tables_query)
                
                table_name = "data"  # Default table name for web connectors
                if tables_result and hasattr(tables_result, 'fetch'):
                    tables_df = tables_result.fetch()
                    if not tables_df.empty and len(tables_df) > 0:
                        # Use the first available table
                        table_name = tables_df.iloc[0]['Tables_in_' + connector_name]
                        logger.info(f"🎯 Found table: {table_name}")
                
            except Exception as e:
                logger.warning(f"⚠️ Could not list tables, using default 'data': {e}")
                table_name = "data"
            
            # Test the connector with the found table name
            test_query = f"SELECT * FROM {connector_name}.{table_name} LIMIT 3"
            
            logger.info(f"🧪 Testing web connector: {test_query}")
            
            result = self.connection.query(test_query)
            
            if result and hasattr(result, 'fetch'):
                df = result.fetch()
                if not df.empty:
                    logger.info(f"✅ Web connector test successful - retrieved {len(df)} rows")
                    return {
                        "success": True,
                        "rows_retrieved": len(df),
                        "columns": list(df.columns),
                        "sample_data": df.head(3).to_dict('records'),
                        "table_name": table_name
                    }
                else:
                    logger.warning(f"⚠️ Web connector test returned no data")
                    return {
                        "success": False,
                        "error": "No data returned from web connector",
                        "table_name": table_name
                    }
            else:
                logger.warning(f"⚠️ Web connector test failed - no result")
                return {
                    "success": False,
                    "error": "Query execution failed"
                }
                
        except Exception as e:
            logger.error(f"❌ Web connector test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def create_dataset_from_web_connector(
        self, 
        connector_name: str, 
        dataset_name: str,
        table_name: str = "data"
    ) -> Dict[str, Any]:
        """Create a dataset view from a web connector."""
        try:
            if not self._ensure_connection():
                return {"success": False, "error": "MindsDB connection not available"}

            # Clean names for MindsDB
            clean_connector = connector_name.lower().replace(' ', '_').replace('-', '_')
            clean_dataset = dataset_name.lower().replace(' ', '_').replace('-', '_')
            
            # Create a view that can be used for ML models
            create_view_sql = f"""
            CREATE OR REPLACE VIEW {clean_dataset}_view AS
            SELECT * FROM {clean_connector}.{table_name};
            """
            
            logger.info(f"📊 Creating dataset view: {clean_dataset}_view")
            logger.info(f"📄 SQL: {create_view_sql}")
            
            result = self.connection.query(create_view_sql)
            
            # Test the view
            test_query = f"SELECT * FROM {clean_dataset}_view LIMIT 5"
            test_result = self.connection.query(test_query)
            
            sample_data = []
            columns = []
            row_count = 0
            
            if test_result and hasattr(test_result, 'fetch'):
                df = test_result.fetch()
                if not df.empty:
                    sample_data = df.head(5).to_dict('records')
                    columns = list(df.columns)
                    
                    # Try to get total row count
                    try:
                        count_query = f"SELECT COUNT(*) as total_rows FROM {clean_dataset}_view"
                        count_result = self.connection.query(count_query)
                        count_df = count_result.fetch()
                        if not count_df.empty:
                            row_count = count_df.iloc[0]['total_rows']
                    except:
                        row_count = len(df)
            
            logger.info(f"✅ Dataset view {clean_dataset}_view created successfully")
            
            return {
                "success": True,
                "view_name": f"{clean_dataset}_view",
                "connector_name": clean_connector,
                "columns": columns,
                "sample_data": sample_data,
                "estimated_rows": row_count,
                "message": f"Dataset view {clean_dataset}_view created from web connector"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create dataset from web connector: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def create_file_database_connector(self, file_upload: "FileUpload") -> Dict[str, Any]:
        """Create MindsDB database connector for uploaded files to make them accessible."""
        try:
            if not self._ensure_connection():
                return {"success": False, "error": "MindsDB connection not available"}

            # Generate clean database name for the file
            clean_name = f"file_db_{file_upload.id}"
            
            # Determine the appropriate engine and parameters based on file type
            file_ext = os.path.splitext(file_upload.original_filename.lower())[1].lstrip('.')
            
            if file_ext in ['csv', 'tsv']:
                # Use files engine for CSV/TSV files
                connection_params = {
                    "file": file_upload.file_path
                }
                engine = "files"
            elif file_ext in ['xlsx', 'xls']:
                # Use files engine for Excel files  
                connection_params = {
                    "file": file_upload.file_path
                }
                engine = "files"
            elif file_ext in ['json']:
                # Use files engine for JSON files
                connection_params = {
                    "file": file_upload.file_path
                }
                engine = "files"
            elif file_ext in ['parquet']:
                # Use files engine for Parquet files
                connection_params = {
                    "file": file_upload.file_path
                }
                engine = "files"
            else:
                # Default to files engine for other file types
                connection_params = {
                    "file": file_upload.file_path
                }
                engine = "files"

            # Create the database connector using MindsDB SQL
            create_db_sql = f"""
            CREATE DATABASE IF NOT EXISTS {clean_name}
            WITH ENGINE = '{engine}',
            PARAMETERS = {json.dumps(connection_params)};
            """
            
            logger.info(f"🗄️ Creating file database connector: {clean_name}")
            logger.info(f"📄 SQL: {create_db_sql}")
            
            try:
                result = self.connection.query(create_db_sql)
                logger.info(f"✅ File database connector {clean_name} created successfully")
                
                # Test the connector by trying to fetch data
                test_result = self.test_file_database_connector(clean_name, file_upload)
                
                return {
                    "success": True,
                    "database_name": clean_name,
                    "engine": engine,
                    "file_path": file_upload.file_path,
                    "file_type": file_ext,
                    "test_result": test_result,
                    "message": f"File database connector {clean_name} created successfully"
                }
                
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"✅ File database connector {clean_name} already exists")
                    return {
                        "success": True,
                        "database_name": clean_name,
                        "engine": engine,
                        "file_path": file_upload.file_path,
                        "file_type": file_ext,
                        "message": f"File database connector {clean_name} already exists"
                    }
                else:
                    raise e
                    
        except Exception as e:
            logger.error(f"❌ Failed to create file database connector for {file_upload.original_filename}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_upload_id": file_upload.id
            }

    def test_file_database_connector(self, database_name: str, file_upload: "FileUpload") -> Dict[str, Any]:
        """Test a file database connector by fetching sample data."""
        try:
            if not self._ensure_connection():
                return {"success": False, "error": "MindsDB connection not available"}

            # Try different table names that MindsDB might use for file data
            possible_table_names = [
                file_upload.original_filename.split('.')[0],  # filename without extension
                "data",  # common default
                "file",  # another common default
                f"uploaded_file_{file_upload.id}"  # our custom name
            ]
            
            for table_name in possible_table_names:
                try:
                    # Clean table name for SQL
                    clean_table = table_name.lower().replace(' ', '_').replace('-', '_')
                    test_query = f"SELECT * FROM {database_name}.{clean_table} LIMIT 3"
                    
                    logger.info(f"🧪 Testing file database connector: {test_query}")
                    
                    result = self.connection.query(test_query)
                    
                    if result and hasattr(result, 'fetch'):
                        df = result.fetch()
                        if not df.empty:
                            logger.info(f"✅ File database test successful with table '{clean_table}' - retrieved {len(df)} rows")
                            return {
                                "success": True,
                                "table_name": clean_table,
                                "rows_retrieved": len(df),
                                "columns": list(df.columns),
                                "sample_data": df.head(3).to_dict('records')
                            }
                except Exception as table_error:
                    logger.debug(f"Table '{clean_table}' not found: {table_error}")
                    continue
            
            # If no table worked, return partial success (database exists but no accessible tables)
            logger.warning(f"⚠️ File database connector created but no accessible tables found")
            return {
                "success": True,
                "warning": "Database created but no accessible tables found",
                "tried_tables": possible_table_names
            }
                
        except Exception as e:
            logger.error(f"❌ File database connector test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def chat_with_dataset(self, dataset_id: str, message: str, user_id: Optional[int] = None, session_id: Optional[str] = None, organization_id: Optional[int] = None) -> Dict[str, Any]:
        """Chat with dataset using MindsDB connectors and native AI models."""
        try:
            import time
            start_time = time.time()
            
            logger.info(f"🔍 Starting chat_with_dataset for dataset_id={dataset_id}, message='{message[:50]}...'")
            
            # Get dataset information from database
            dataset = None
            dataset_context = ""
            is_web_connector = False
            web_connector_info = {}
            
            try:
                from app.core.database import get_db
                from app.models.dataset import Dataset
                from sqlalchemy.orm import Session
                
                db = next(get_db())
                dataset = db.query(Dataset).filter(Dataset.id == int(dataset_id)).first()
                
                if not dataset:
                    logger.error(f"❌ Dataset with ID {dataset_id} not found")
                    return {
                        "error": f"Dataset with ID {dataset_id} not found",
                        "answer": "I couldn't find the dataset you're referring to. Please check the dataset ID.",
                        "dataset_id": dataset_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                logger.info(f"🔍 Processing chat for dataset: {dataset.name} (ID: {dataset_id})")
                
                # Check if this is a web connector dataset
                if dataset.connector_id or dataset.source_url:
                    is_web_connector = True
                    web_connector_info = {
                        "connector_id": dataset.connector_id,
                        "source_url": dataset.source_url,
                        "connector_name": getattr(dataset, 'connector_name', None)
                    }
                    logger.info(f"🌐 Detected web connector dataset: {web_connector_info}")
                
            except Exception as db_error:
                logger.error(f"❌ Could not load dataset from database: {db_error}")
                return {
                    "error": f"Database error: {str(db_error)}",
                    "answer": "I encountered a database error while trying to access the dataset.",
                    "dataset_id": dataset_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Ensure MindsDB connection
            logger.info("🔗 Checking MindsDB connection...")
            if not self._ensure_connection():
                logger.error("❌ MindsDB connection failed")
                return {
                    "error": "MindsDB connection failed",
                    "answer": "I couldn't connect to MindsDB to process your request. Please try again later.",
                    "dataset_id": dataset_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            logger.info("✅ MindsDB connection established")
            
            # Build enhanced dataset context based on type
            if is_web_connector:
                dataset_context = f"""
                Dataset Information (Web Connector):
                - Name: {dataset.name}
                - Type: {dataset.type} (Web API Data)
                - Description: {dataset.description or 'No description available'}
                - Data Source: External API via web connector
                - Source URL: {dataset.source_url}
                - Connector ID: {dataset.connector_id}
                - Rows: {dataset.row_count or 'Dynamic (API-dependent)'}
                - Columns: {dataset.column_count or 'Dynamic (API-dependent)'}
                - Created: {dataset.created_at}
                - Data Access: Real-time via MindsDB web connector
                - Data Freshness: Live data from API endpoint
                """
                
                # Try to get fresh sample data from the web connector
                try:
                    clean_dataset = dataset.name.lower().replace(' ', '_').replace('-', '_')
                    sample_query = f"SELECT * FROM {clean_dataset}_view LIMIT 5"
                    sample_result = self.connection.query(sample_query)
                    
                    if sample_result and hasattr(sample_result, 'fetch'):
                        sample_df = sample_result.fetch()
                        if not sample_df.empty:
                            sample_data = sample_df.to_dict('records')
                            dataset_context += f"\n- Current Sample Data: {sample_data[:2]}"  # Show first 2 rows
                            dataset_context += f"\n- Available Columns: {list(sample_df.columns)}"
                            logger.info(f"📊 Retrieved fresh sample data from web connector")
                        else:
                            dataset_context += "\n- Sample Data: No data currently available from API"
                    else:
                        dataset_context += "\n- Sample Data: Unable to fetch current data"
                        
                except Exception as sample_error:
                    logger.warning(f"⚠️ Could not fetch sample data from web connector: {sample_error}")
                    dataset_context += "\n- Sample Data: Unable to fetch current data from web connector"
                    
            else:
                # For uploaded files, ensure they have a database connector
                logger.info(f"🗄️ Processing uploaded file dataset: {dataset.name}")
                
                # Get the file upload record
                file_upload = None
                try:
                    from app.models.file_handler import FileUpload
                    file_upload = db.query(FileUpload).filter(
                        FileUpload.dataset_id == dataset.id
                    ).first()
                    
                    if file_upload:
                        logger.info(f"📁 Found file upload record: {file_upload.original_filename}")
                        
                        # Create database connector for this file if it doesn't exist
                        connector_result = self.create_file_database_connector(file_upload)
                        
                        if connector_result.get("success"):
                            logger.info(f"✅ Database connector ready: {connector_result.get('database_name')}")
                            
                            # Try to get sample data from the file database
                            database_name = connector_result.get("database_name")
                            test_result = connector_result.get("test_result", {})
                            
                            if test_result.get("success") and test_result.get("sample_data"):
                                sample_data = test_result.get("sample_data", [])
                                columns = test_result.get("columns", [])
                                
                                dataset_context = f"""
                Dataset Information (Uploaded File):
                - Name: {dataset.name}
                - Type: {dataset.type}
                - Description: {dataset.description or 'No description available'}
                - Data Source: Uploaded file ({file_upload.original_filename})
                - File Size: {file_upload.file_size} bytes
                - Rows: {dataset.row_count or test_result.get('rows_retrieved', 'Unknown')}
                - Columns: {dataset.column_count or len(columns)}
                - Created: {dataset.created_at}
                - Data Access: Static file data via MindsDB file connector
                - Database Name: {database_name}
                - Available Columns: {columns}
                - Sample Data: {sample_data[:2] if sample_data else 'No sample data available'}
                """
                            else:
                                dataset_context = f"""
                Dataset Information (Uploaded File):
                - Name: {dataset.name}
                - Type: {dataset.type}
                - Description: {dataset.description or 'No description available'}
                - Data Source: Uploaded file ({file_upload.original_filename})
                - File Size: {file_upload.file_size} bytes
                - Rows: {dataset.row_count or 'Unknown'}
                - Columns: {dataset.column_count or 'Unknown'}
                - Created: {dataset.created_at}
                - Data Access: Static file data via MindsDB file connector
                - Database Name: {database_name}
                - Note: Database connector created but data access needs verification
                """
                        else:
                            logger.warning(f"⚠️ Failed to create database connector: {connector_result.get('error')}")
                            dataset_context = f"""
                Dataset Information (Uploaded File):
                - Name: {dataset.name}
                - Type: {dataset.type}
                - Description: {dataset.description or 'No description available'}
                - Data Source: Uploaded file ({file_upload.original_filename})
                - File Size: {file_upload.file_size} bytes
                - Rows: {dataset.row_count or 'Unknown'}
                - Columns: {dataset.column_count or 'Unknown'}
                - Created: {dataset.created_at}
                - Data Access: File data (connector creation failed)
                - Warning: Database connector could not be created - {connector_result.get('error')}
                """
                    else:
                        logger.warning(f"⚠️ No file upload record found for dataset {dataset.id}")
                        dataset_context = f"""
                Dataset Information (Uploaded File):
                - Name: {dataset.name}
                - Type: {dataset.type}
                - Description: {dataset.description or 'No description available'}
                - Data Source: Uploaded file
                - Rows: {dataset.row_count or 'Unknown'}
                - Columns: {dataset.column_count or 'Unknown'}
                - Created: {dataset.created_at}
                - Data Access: Static file data
                - Warning: File upload record not found
                """
                        
                except Exception as file_error:
                    logger.error(f"❌ Error processing file upload for dataset {dataset.id}: {file_error}")
                    dataset_context = f"""
                Dataset Information (Uploaded File):
                - Name: {dataset.name}
                - Type: {dataset.type}
                - Description: {dataset.description or 'No description available'}
                - Data Source: Uploaded file
                - Rows: {dataset.row_count or 'Unknown'}
                - Columns: {dataset.column_count or 'Unknown'}
                - Created: {dataset.created_at}
                - Data Access: Static file data
                - Error: Could not process file upload - {str(file_error)}
                """
            
            # Build enhanced prompt based on dataset type
            if is_web_connector:
                enhanced_message = f"""
                You are an expert data analyst with access to a live API dataset through MindsDB web connectors. Your role is to provide comprehensive, actionable insights with detailed analysis and real-time data understanding.

                LIVE API DATASET INFORMATION:
                {dataset_context}

                USER QUESTION: {message}

                IMPORTANT CONTEXT FOR WEB CONNECTOR DATASETS:
                - This dataset contains LIVE data from an external API endpoint
                - Data may change between queries as it's fetched in real-time
                - The data structure and content depend on the API's current response
                - You have access to the most current data available from the API
                - Consider API limitations, rate limits, and data freshness in your analysis

                INSTRUCTIONS FOR YOUR RESPONSE:
                1. **Live Data Understanding**: Explain that this is real-time API data and its implications
                2. **Current Data Analysis**: Provide analysis based on the most recent data available
                3. **API Data Patterns**: Identify patterns specific to API-sourced data
                4. **Real-time Insights**: Focus on insights that leverage the live nature of the data
                5. **Data Freshness**: Comment on data recency and potential changes over time
                6. **API Considerations**: Note any API-specific limitations or characteristics

                RESPONSE FORMAT:
                Please structure your response using clear markdown formatting with the following sections:

                ## 🌐 Live API Dataset Overview
                [Description of the real-time dataset and its API source characteristics]

                ## 🎯 Current Data Analysis
                [Analysis based on the most recent data from the API]

                ## 📊 Real-time Data Patterns
                [Patterns and trends specific to this live API data]

                ## 📈 Dynamic Insights
                [Insights that leverage the real-time nature of the data]

                ## 🔄 Data Freshness & Reliability
                [Information about data recency and API reliability]

                ## 💡 API-Aware Recommendations
                [Recommendations that consider the live, API-based nature of the data]

                ## ⚠️ API Limitations & Considerations
                [Any API-specific limitations, rate limits, or data quality considerations]

                Focus on providing insights that are enhanced by the real-time, API-based nature of this dataset. Emphasize current data states and dynamic analysis capabilities.
                """
            else:
                enhanced_message = f"""
                You are an expert data analyst with access to a specific uploaded dataset. Your role is to provide comprehensive, actionable insights with detailed analysis and visualization recommendations.

                DATASET INFORMATION:
                {dataset_context}

                USER QUESTION: {message}

                INSTRUCTIONS FOR YOUR RESPONSE:
                1. **Data Understanding**: First, clearly explain what this dataset contains and its structure
                2. **Direct Answer**: Provide a specific, detailed answer to the user's question based on the actual data
                3. **Statistical Analysis**: Include relevant statistics, patterns, and trends you can identify
                4. **Visualization Recommendations**: Suggest specific charts and graphs that would best represent the data for this question
                5. **Actionable Insights**: Provide practical insights and recommendations based on your analysis
                6. **Data Quality Notes**: Comment on any data quality issues or limitations you observe

                RESPONSE FORMAT:
                Please structure your response using clear markdown formatting with the following sections:

                ## 📊 Data Overview
                [Brief description of the dataset and its key characteristics]

                ## 🎯 Analysis Results
                [Direct answer to the user's question with specific findings]

                ## 📈 Statistical Insights
                [Key statistics, patterns, and trends identified]

                ## 📋 Recommended Visualizations
                [Specific chart types and visualization suggestions with reasoning]

                ## 💡 Key Insights & Recommendations
                [Actionable insights and practical recommendations]

                ## ⚠️ Data Quality & Limitations
                [Any limitations or data quality considerations]

                Be specific, use actual data values when available, and ensure your analysis is thorough and professional. Focus on providing value through deep data understanding rather than generic responses.
                """
            
            logger.info(f"💬 Using {'web connector enhanced' if is_web_connector else 'general'} chat model: {self.chat_model_name}")
            
            # Use existing general chat model with enhanced context
            result = self.ai_chat(enhanced_message, model_name=self.chat_model_name)
            
            if result and isinstance(result, dict) and result.get("answer"):
                response_time = time.time() - start_time
                result.update({
                    "dataset_id": dataset_id,
                    "dataset_name": dataset.name,
                    "model": f"enhanced_{self.chat_model_name}",
                    "source": "mindsdb_web_connector_chat" if is_web_connector else "mindsdb_enhanced_chat",
                    "is_web_connector": is_web_connector,
                    "web_connector_info": web_connector_info if is_web_connector else None,
                    "response_time_seconds": response_time,
                    "user_id": user_id,
                    "session_id": session_id,
                    "organization_id": organization_id or dataset.organization_id
                })
                
                logger.info(f"✅ Successfully processed {'web connector' if is_web_connector else 'standard'} dataset chat in {response_time:.2f}s")
                return result
            else:
                logger.error("❌ AI chat returned no valid response")
                return {
                    "error": "AI chat failed",
                    "answer": "I'm sorry, but I couldn't process your question at this time. Please try again.",
                    "dataset_id": dataset_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Dataset chat failed: {e}")
            return {
                "error": f"Dataset chat failed: {str(e)}",
                "answer": "I'm sorry, but I encountered an error while processing your question.",
                "dataset_id": dataset_id,
                "timestamp": datetime.utcnow().isoformat()
            }

    def create_dataset_ml_model(
        self, 
        dataset_id: int, 
        dataset_name: str, 
        dataset_type: str, 
        dataset_content: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create ML models for a dataset (chat model with Gemini)."""
        try:
            logger.info(f"🤖 Creating ML models for dataset {dataset_id} ({dataset_name})")
            
            # Ensure MindsDB connection
            if not self._ensure_connection():
                logger.error("❌ MindsDB connection failed")
                return {
                    "success": False,
                    "error": "MindsDB connection failed",
                    "dataset_id": dataset_id
                }
            
            # Clean dataset name for MindsDB model naming
            clean_dataset_name = dataset_name.lower().replace(' ', '_').replace('-', '_')
            model_name = f"dataset_{dataset_id}_chat_model"
            
            # Create chat model using Gemini engine
            prompt_template = f"""You are an AI assistant specialized in analyzing and discussing the dataset "{dataset_name}".

Dataset Information:
- Name: {dataset_name}
- Type: {dataset_type}
- Dataset ID: {dataset_id}

You are designed to help users understand and analyze this specific dataset. When answering questions:
1. Be specific about this dataset
2. Provide helpful insights when possible
3. Explain any patterns or concepts clearly
4. Suggest relevant analyses or questions
5. Be helpful and informative

User Question: {{{{question}}}}

Please provide a comprehensive answer about this dataset:"""

            # Create the chat model
            chat_model_result = self.create_gemini_model(
                model_name=model_name,
                model_type="chat",
                column_name="response"
            )
            
            # Update the model with specific prompt template if creation was successful
            if chat_model_result.get("status") == "created":
                try:
                    # Try to set a custom prompt template for this specific dataset
                    update_query = f"""
                    CREATE OR REPLACE MODEL {model_name}
                    PREDICT response
                    USING
                        engine = '{self.engine_name}',
                        model_name = '{self.default_model}',
                        prompt_template = '{prompt_template}',
                        max_tokens = 1500;
                    """
                    
                    self.connection.query(update_query)
                    logger.info(f"✅ Updated chat model {model_name} with dataset-specific prompt")
                    
                except Exception as update_error:
                    logger.warning(f"⚠️ Could not update model prompt template: {update_error}")
                    # Continue anyway - model was created successfully
            
            logger.info(f"✅ ML models created for dataset {dataset_id}")
            
            return {
                "success": True,
                "models_created": [
                    {
                        "name": model_name,
                        "type": "chat",
                        "engine": self.engine_name,
                        "status": chat_model_result.get("status", "unknown")
                    }
                ],
                "dataset_id": dataset_id,
                "dataset_name": dataset_name
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create ML models for dataset {dataset_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "dataset_id": dataset_id
            }

    def delete_dataset_models(self, dataset_id: int) -> Dict[str, Any]:
        """Delete all MindsDB models associated with a dataset."""
        try:
            logger.info(f"🗑️ Deleting ML models for dataset {dataset_id}")
            
            # Ensure MindsDB connection
            if not self._ensure_connection():
                logger.error("❌ MindsDB connection failed")
                return {
                    "success": False,
                    "error": "MindsDB connection failed",
                    "dataset_id": dataset_id
                }
            
            deleted_models = []
            errors = []
            
            # List of model patterns to look for and delete
            model_patterns = [
                f"dataset_{dataset_id}_chat_model",
                f"dataset_{dataset_id}_model",
                f"dataset_{dataset_id}_embedding_model",
                f"dataset_{dataset_id}_vision_model"
            ]
            
            for model_name in model_patterns:
                try:
                    # Check if model exists
                    check_query = f"SHOW MODELS WHERE name = '{model_name}'"
                    result = self.connection.query(check_query)
                    
                    if result and hasattr(result, 'fetch'):
                        models_df = result.fetch()
                        if not models_df.empty:
                            # Model exists, delete it
                            logger.info(f"🗑️ Deleting model: {model_name}")
                            delete_query = f"DROP MODEL {model_name}"
                            self.connection.query(delete_query)
                            deleted_models.append(model_name)
                            logger.info(f"✅ Successfully deleted model: {model_name}")
                        else:
                            logger.info(f"ℹ️ Model {model_name} does not exist, skipping")
                    else:
                        logger.info(f"ℹ️ Could not check existence of model {model_name}, attempting delete anyway")
                        
                        # Try to delete anyway in case the check failed
                        try:
                            delete_query = f"DROP MODEL IF EXISTS {model_name}"
                            self.connection.query(delete_query)
                            deleted_models.append(model_name)
                            logger.info(f"✅ Successfully deleted model: {model_name}")
                        except Exception as delete_error:
                            error_msg = str(delete_error)
                            if "does not exist" not in error_msg.lower():
                                logger.warning(f"⚠️ Could not delete model {model_name}: {error_msg}")
                                errors.append(f"{model_name}: {error_msg}")
                            else:
                                logger.info(f"ℹ️ Model {model_name} does not exist")
                        
                except Exception as e:
                    error_msg = str(e)
                    if "does not exist" not in error_msg.lower():
                        logger.warning(f"⚠️ Error checking/deleting model {model_name}: {error_msg}")
                        errors.append(f"{model_name}: {error_msg}")
                    else:
                        logger.info(f"ℹ️ Model {model_name} does not exist")
            
            # Also clean up any other models that might follow different naming patterns
            try:
                # Get all models and find any that contain the dataset ID
                all_models_query = "SHOW MODELS"
                result = self.connection.query(all_models_query)
                
                if result and hasattr(result, 'fetch'):
                    all_models_df = result.fetch()
                    
                    # Look for models that contain the dataset ID
                    dataset_models = all_models_df[
                        all_models_df['NAME'].str.contains(f"dataset_{dataset_id}", case=False, na=False) |
                        all_models_df['NAME'].str.contains(f"_{dataset_id}_", case=False, na=False)
                    ]
                    
                    for _, model_row in dataset_models.iterrows():
                        model_name = model_row['NAME']
                        if model_name not in deleted_models:
                            try:
                                logger.info(f"🗑️ Deleting additional dataset model: {model_name}")
                                delete_query = f"DROP MODEL {model_name}"
                                self.connection.query(delete_query)
                                deleted_models.append(model_name)
                                logger.info(f"✅ Successfully deleted additional model: {model_name}")
                            except Exception as delete_error:
                                error_msg = str(delete_error)
                                logger.warning(f"⚠️ Could not delete additional model {model_name}: {error_msg}")
                                errors.append(f"{model_name}: {error_msg}")
                
            except Exception as e:
                logger.warning(f"⚠️ Could not check for additional dataset models: {e}")
                errors.append(f"Additional model check failed: {str(e)}")
            
            result = {
                "success": len(deleted_models) > 0 or len(errors) == 0,
                "deleted_models": deleted_models,
                "errors": errors,
                "dataset_id": dataset_id
            }
            
            if deleted_models:
                logger.info(f"✅ Successfully deleted {len(deleted_models)} models for dataset {dataset_id}: {deleted_models}")
            else:
                logger.info(f"ℹ️ No models found to delete for dataset {dataset_id}")
                
            if errors:
                logger.warning(f"⚠️ Some errors occurred while deleting models for dataset {dataset_id}: {errors}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to delete models for dataset {dataset_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "dataset_id": dataset_id,
                "deleted_models": [],
                "errors": [str(e)]
            }


# Create service instance
mindsdb_service = MindsDBService()