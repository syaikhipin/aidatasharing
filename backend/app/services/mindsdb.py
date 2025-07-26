import mindsdb_sdk
import google.generativeai as genai
from typing import Dict, List, Optional, Any
from app.core.config import settings
import logging
import json
from datetime import datetime
import time
import requests

logger = logging.getLogger(__name__)


class MindsDBService:
    def __init__(self):
        # Use settings from environment
        self.base_url = settings.MINDSDB_URL
        self.api_key = settings.GOOGLE_API_KEY
        
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

    def create_gemini_engine(self) -> Dict[str, Any]:
        """Create or verify Google Gemini engine using raw SQL."""
        try:
            if not self._ensure_connection():
                return {"message": "SDK connection not available", "status": "error"}

            # Use raw SQL to create the engine
            create_engine_sql = f"""
            CREATE ML_ENGINE IF NOT EXISTS {self.engine_name}
            FROM google_gemini
            USING
                api_key = '{self.api_key}';
            """
            
            try:
                # Execute raw SQL instead of using SDK methods
                self.connection.query(create_engine_sql)
                logger.info(f"✅ Engine {self.engine_name} created/verified successfully")
                return {
                    "message": f"Engine {self.engine_name} ready",
                    "status": "exists",
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

            # Set default column name
            if not column_name:
                column_name = "question"

            # Create model using raw SQL with proper project context
            create_model_sql = f"""
            CREATE MODEL {model_name}
            PREDICT answer
            USING
                engine = '{self.engine_name}',
                model = '{self.default_model}';
            """
            
            try:
                self.connection.query(create_model_sql)
                logger.info(f"✅ Created Gemini model: {model_name}")
                
                return {
                    "message": f"Model {model_name} created successfully",
                    "status": "created",
                    "model_name": model_name,
                    "engine": self.engine_name,
                    "column": column_name,
                    "model": self.default_model
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
        """Handle AI chat using MindsDB with Gemini integration."""
        if not model_name:
            model_name = self.chat_model_name

        try:
            # Only use MindsDB for chat - no fallback to direct API
            if self._ensure_connection() and self.connection:
                try:
                    logger.info(f"💬 Using MindsDB for chat with model: {model_name}")
                    
                    # First ensure the model exists and is ready
                    model_result = self.create_gemini_model(model_name)
                    if model_result.get("status") == "error":
                        logger.error(f"❌ Failed to create/verify model {model_name}: {model_result.get('message')}")
                        return {
                            "answer": f"I'm sorry, but I couldn't initialize the AI model: {model_result.get('message')}",
                            "error": f"Model creation failed: {model_result.get('message')}",
                            "model": f"{model_name} (MindsDB Error)",
                            "timestamp": datetime.utcnow().isoformat(),
                            "source": "mindsdb_model_error"
                        }
                    
                    # Wait a moment for the model to be ready
                    import time
                    time.sleep(2)
                    
                    # Check if model is ready by querying model status
                    try:
                        status_query = f"DESCRIBE mindsdb.{model_name}"
                        status_result = self.connection.query(status_query)
                        logger.info(f"🔍 Model status query executed")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not check model status: {e}")
                    
                    # Query the model using MindsDB - Gemini models use 'response' column
                    query = f"""
                    SELECT response 
                    FROM {model_name} 
                    WHERE question = '{message.replace("'", "''")}'
                    """
                    
                    logger.info(f"🔍 Executing MindsDB query: {query}")
                    result = self.connection.query(query)
                    logger.info(f"🔍 Query result type: {type(result)}")
                    
                    if result:
                        try:
                            # Try different methods to fetch data
                            if hasattr(result, 'fetch_all'):
                                rows = result.fetch_all()
                                logger.info(f"🔍 fetch_all() returned {len(rows) if rows else 0} rows")
                            elif hasattr(result, 'fetch'):
                                rows = result.fetch()
                                logger.info(f"🔍 fetch() returned: {type(rows)}")
                                if hasattr(rows, 'to_dict'):
                                    rows = [rows.to_dict()]
                                elif not isinstance(rows, list):
                                    rows = [rows] if rows is not None else []
                            else:
                                logger.warning(f"⚠️ Result object has no fetch method: {dir(result)}")
                                rows = []
                            
                            if rows and len(rows) > 0:
                                logger.info(f"🔍 First row content: {rows[0]}")
                                # MindsDB Gemini models use 'response' column, not 'answer'
                                row_data = rows[0]
                                answer = ""
                                
                                if isinstance(row_data, dict):
                                    answer = row_data.get('response', '')
                                else:
                                    answer = str(row_data)
                                
                                # Handle case where answer might be a complex object
                                if not isinstance(answer, str):
                                    answer = str(answer)
                                
                                # Clean up the response format if it's a pandas Series representation
                                if answer.startswith("{0: '") and answer.endswith("'}"):
                                    # Extract the actual response from pandas Series format
                                    answer = answer[5:-2]  # Remove "{0: '" and "'}"
                                elif answer.startswith("{0: \"") and answer.endswith("\"}"):
                                    # Handle double quotes
                                    answer = answer[5:-2]  # Remove "{0: \"" and "\"}"
                                
                                # Clean up newlines
                                answer = answer.replace('\\n', '\n').strip()
                                
                                if answer and answer.strip():
                                    return {
                                        "answer": answer,
                                        "model": f"{model_name} (MindsDB)",
                                        "timestamp": datetime.utcnow().isoformat(),
                                        "tokens_used": len(message.split()) + len(answer.split()),
                                        "source": "mindsdb"
                                    }
                                else:
                                    logger.warning(f"⚠️ MindsDB query returned empty response for model {model_name}")
                            else:
                                logger.warning(f"⚠️ MindsDB query returned no rows for model {model_name}")
                                
                        except Exception as fetch_error:
                            logger.error(f"❌ Error fetching MindsDB result: {fetch_error}")
                    
                    # If we get here, the query didn't return a valid answer
                    logger.warning(f"⚠️ MindsDB query returned no valid result for model {model_name}")
                    return {
                        "answer": "I'm sorry, but I couldn't generate a response for your question. The MindsDB model may need more time to initialize or there might be an issue with the query.",
                        "error": "No valid answer returned from MindsDB",
                        "model": f"{model_name} (MindsDB)",
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "mindsdb_empty"
                    }
                
                except Exception as e:
                    logger.error(f"❌ MindsDB chat failed: {e}")
                    return {
                        "answer": f"I'm sorry, but I encountered an error while processing your question through MindsDB: {str(e)}",
                        "error": f"MindsDB chat failed: {str(e)}",
                        "model": f"{model_name} (MindsDB Error)",
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "mindsdb_error"
                    }
            else:
                logger.error("❌ MindsDB connection not available")
                return {
                    "answer": "I'm sorry, but I couldn't connect to MindsDB. Please ensure the MindsDB service is running and properly configured.",
                    "error": "MindsDB connection not available",
                    "model": "Connection Error",
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "connection_error"
                }

        except Exception as e:
            logger.error(f"❌ AI chat failed: {e}")
            return {
                "answer": f"I'm sorry, but I encountered an error: {str(e)}",
                "error": f"Chat failed: {str(e)}",
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "general_error"
            }



    def create_dataset_ml_model(
        self, 
        dataset_id: int, 
        dataset_name: str, 
        dataset_type: str = "CSV",
        dataset_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create ML model for dataset analysis with enhanced file type support."""
        try:
            # Check if MindsDB connection is available
            if not self._ensure_connection() or self.connection is None:
                logger.error(f"❌ MindsDB connection not available for dataset {dataset_id}")
                return {
                    "success": False,
                    "error": "MindsDB connection not available. Please ensure MindsDB is running and properly configured.",
                    "dataset_id": dataset_id,
                    "dataset_name": dataset_name,
                    "file_type": dataset_type
                }
            
            # Generate model name for the dataset
            chat_model = f"dataset_{dataset_id}_chat"
            
            # Enhanced model creation based on file type
            if dataset_type.upper() in ["PDF", "JSON"]:
                # For PDF and JSON, create specialized models
                model_result = self._create_enhanced_model(
                    model_name=chat_model,
                    dataset_type=dataset_type,
                    dataset_content=dataset_content
                )
            else:
                # Standard model for CSV and other formats
                model_result = self.create_gemini_model(
                    model_name=chat_model,
                    model_type="dataset_chat",
                    column_name="question"
                )
            
            if model_result.get("status") in ["created", "exists"]:
                logger.info(f"✅ Dataset model created: {chat_model}")
                return {
                    "success": True,
                    "message": f"ML model created for dataset {dataset_name}",
                    "chat_model": chat_model,
                    "engine": self.engine_name,
                    "dataset_id": dataset_id,
                    "dataset_name": dataset_name,
                    "file_type": dataset_type
                }
            else:
                logger.error(f"❌ Dataset model creation failed: {model_result}")
                return {
                    "success": False,
                    "error": f"Model creation failed: {model_result.get('message', 'Unknown error')}",
                    "dataset_id": dataset_id
                }
                
        except Exception as e:
            logger.error(f"❌ Dataset model creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "dataset_id": dataset_id
            }

    def _create_enhanced_model(
        self,
        model_name: str,
        dataset_type: str,
        dataset_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create enhanced models for PDF and JSON files."""
        try:
            # Check if MindsDB is available
            if not self._ensure_connection() or self.connection is None:
                logger.warning(f"⚠️ MindsDB connection not available for enhanced model, using fallback")
                return {
                    "message": "MindsDB not available, using direct Gemini API",
                    "status": "fallback",
                    "model_name": model_name
                }
            
            # Enhanced system prompt based on file type
            if dataset_type.upper() == "PDF":
                system_prompt = """
                You are an AI assistant specialized in analyzing PDF documents. 
                You can extract text, understand document structure, identify key information,
                and answer questions about the document content. When analyzing PDFs, consider:
                - Document sections and hierarchy
                - Tables and structured data
                - Text formatting and emphasis
                - Images and captions (if mentioned)
                """
            elif dataset_type.upper() == "JSON":
                system_prompt = """
                You are an AI assistant specialized in analyzing JSON data structures.
                You can understand nested objects, arrays, data types, and relationships.
                When analyzing JSON, consider:
                - Data structure and schema
                - Nested relationships
                - Array patterns and repetitions
                - Data types and validation
                - Missing or null values
                """
            else:
                system_prompt = "You are an AI assistant for data analysis."

            # Create model with enhanced configuration
            create_model_sql = f"""
            CREATE MODEL IF NOT EXISTS mindsdb.{model_name}
            PREDICT answer
            USING
                engine = '{self.engine_name}',
                model = '{self.default_model}',
                mode = 'conversational',
                system_prompt = '{system_prompt}',
                user_column = 'question',
                assistant_column = 'answer';
            """
            
            try:
                self.connection.query(create_model_sql)
                logger.info(f"✅ Created enhanced {dataset_type} model: {model_name}")
            except Exception as e:
                logger.error(f"❌ Failed to create enhanced model: {e}")
                return {
                    "message": f"Failed to create enhanced model: {e}",
                    "status": "fallback",
                    "model_name": model_name
                }
            
            return {
                "message": f"Enhanced {dataset_type} model {model_name} created successfully",
                "status": "created",
                "model_name": model_name,
                "engine": self.engine_name,
                "file_type": dataset_type
            }
            
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"✅ Enhanced model {model_name} already exists")
                return {
                    "message": f"Enhanced model {model_name} ready",
                    "status": "exists",
                    "model_name": model_name
                }
            else:
                raise e

    def process_file_content(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Process different file types and extract content."""
        try:
            if file_type.upper() == "PDF":
                return self._process_pdf_file(file_path)
            elif file_type.upper() == "JSON":
                return self._process_json_file(file_path)
            elif file_type.upper() == "CSV":
                return self._process_csv_file(file_path)
            else:
                return {"success": False, "error": f"Unsupported file type: {file_type}"}
                
        except Exception as e:
            logger.error(f"Error processing {file_type} file {file_path}: {e}")
            return {"success": False, "error": str(e)}

    def _process_pdf_file(self, file_path: str) -> Dict[str, Any]:
        """Process PDF file and extract text content."""
        try:
            import fitz  # PyMuPDF
            
            # Open PDF document
            doc = fitz.open(file_path)
            
            text_content = ""
            page_count = len(doc)
            
            # Extract text from all pages
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                text = page.get_text()
                text_content += f"\n--- Page {page_num + 1} ---\n{text}\n"
            
            doc.close()
            
            # Basic content analysis
            word_count = len(text_content.split())
            char_count = len(text_content)
            
            return {
                "success": True,
                "content": text_content,
                "metadata": {
                    "page_count": page_count,
                    "word_count": word_count,
                    "char_count": char_count,
                    "has_text": bool(text_content.strip())
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"PDF processing failed: {str(e)}"}

    def _process_json_file(self, file_path: str) -> Dict[str, Any]:
        """Process JSON file and analyze structure."""
        try:
            import json
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Analyze JSON structure
            def analyze_structure(obj, depth=0, max_depth=3):
                if depth > max_depth:
                    return "..."
                
                if isinstance(obj, dict):
                    structure = {}
                    for key, value in obj.items():
                        structure[key] = analyze_structure(value, depth + 1, max_depth)
                    return structure
                elif isinstance(obj, list):
                    if obj:
                        return [analyze_structure(obj[0], depth + 1, max_depth)]
                    return []
                else:
                    return type(obj).__name__
            
            structure = analyze_structure(data)
            
            # Count elements
            def count_elements(obj):
                if isinstance(obj, dict):
                    return sum(count_elements(v) for v in obj.values()) + len(obj)
                elif isinstance(obj, list):
                    return sum(count_elements(item) for item in obj) + len(obj)
                else:
                    return 1
            
            element_count = count_elements(data)
            
            return {
                "success": True,
                "content": json.dumps(data, indent=2, ensure_ascii=False),
                "metadata": {
                    "structure": structure,
                    "element_count": element_count,
                    "top_level_type": type(data).__name__,
                    "size_bytes": len(json.dumps(data))
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"JSON processing failed: {str(e)}"}

    def _process_csv_file(self, file_path: str) -> Dict[str, Any]:
        """Process CSV file and analyze structure."""
        try:
            import pandas as pd
            
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Basic analysis
            row_count = len(df)
            column_count = len(df.columns)
            
            # Get data types and basic stats
            dtype_info = {}
            column_stats = {}
            
            for col in df.columns:
                dtype_info[col] = str(df[col].dtype)
                
                if df[col].dtype in ['int64', 'float64']:
                    column_stats[col] = {
                        "type": "numeric",
                        "min": float(df[col].min()),
                        "max": float(df[col].max()),
                        "mean": float(df[col].mean()),
                        "non_null_count": int(df[col].count())
                    }
                else:
                    column_stats[col] = {
                        "type": "categorical",
                        "unique_count": int(df[col].nunique()),
                        "non_null_count": int(df[col].count()),
                        "top_values": df[col].value_counts().head(3).to_dict()
                    }
            
            # Create a preview of the data
            preview_data = df.head(5).to_string()
            
            # Sample of actual data for AI context
            sample_rows = df.head(3).to_dict('records')
            
            return {
                "success": True,
                "content": preview_data,
                "metadata": {
                    "row_count": row_count,
                    "column_count": column_count,
                    "columns": df.columns.tolist(),
                    "dtypes": dtype_info,
                    "column_stats": column_stats,
                    "sample_data": sample_rows,
                    "total_size": df.memory_usage(deep=True).sum()
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"CSV processing failed: {str(e)}"}

    def chat_with_dataset(self, dataset_id: str, message: str, user_id: Optional[int] = None, session_id: Optional[str] = None, organization_id: Optional[int] = None) -> Dict[str, Any]:
        """Chat with dataset using MindsDB connectors and native AI models."""
        try:
            import time
            start_time = time.time()
            
            logger.info(f"🔍 Starting chat_with_dataset for dataset_id={dataset_id}, message='{message[:50]}...'")
            
            # Get dataset information from database
            dataset = None
            dataset_context = ""
            
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
            
            # For now, use a simpler approach - just use the general chat with dataset context
            # Build dataset context
            dataset_context = f"""
            Dataset Information:
            - Name: {dataset.name}
            - Type: {dataset.type}
            - Description: {dataset.description or 'No description available'}
            - Rows: {dataset.row_count or 'Unknown'}
            - Columns: {dataset.column_count or 'Unknown'}
            - Created: {dataset.created_at}
            """
            
            # Try to get sample data if available
            try:
                if dataset.connector_id and dataset.mindsdb_database and dataset.mindsdb_table_name:
                    # Query database connector
                    sample_query = f"SELECT * FROM {dataset.mindsdb_database}.{dataset.mindsdb_table_name} LIMIT 3"
                    logger.info(f"📊 Querying database connector: {sample_query}")
                    result = self.connection.query(sample_query)
                    if result and hasattr(result, 'fetch'):
                        df = result.fetch()
                        if not df.empty:
                            dataset_context += f"\n\nSample Data:\nColumns: {list(df.columns)}\n"
                            for i, (idx, row) in enumerate(df.iterrows(), 1):
                                dataset_context += f"Row {i}: {dict(row)}\n"
                            logger.info(f"✅ Successfully loaded {len(df)} sample rows from database connector")
                else:
                    # Try file dataset
                    sample_query = f"SELECT * FROM files.dataset_{dataset_id} LIMIT 3"
                    logger.info(f"📁 Querying file dataset: {sample_query}")
                    result = self.connection.query(sample_query)
                    if result and hasattr(result, 'fetch'):
                        df = result.fetch()
                        if not df.empty:
                            dataset_context += f"\n\nSample Data:\nColumns: {list(df.columns)}\n"
                            for i, (idx, row) in enumerate(df.iterrows(), 1):
                                dataset_context += f"Row {i}: {dict(row)}\n"
                            logger.info(f"✅ Successfully loaded {len(df)} sample rows from file dataset")
            except Exception as data_error:
                logger.warning(f"ℹ️ Could not load sample data: {data_error}")
            
            # Use general chat with enhanced context
            enhanced_message = f"""
            You are analyzing a specific dataset. Here is the information about this dataset:
            
            {dataset_context}
            
            User Question: {message}
            
            Please provide a detailed, data-driven response based on this dataset information. Be specific about what you can see in the dataset and provide insights based on the actual data structure and content shown above.
            """
            
            logger.info(f"💬 Using general chat model: {self.chat_model_name}")
            
            # Use existing general chat model
            result = self.ai_chat(enhanced_message, model_name=self.chat_model_name)
            
            if result and isinstance(result, dict) and result.get("answer"):
                response_time = time.time() - start_time
                result.update({
                    "dataset_id": dataset_id,
                    "dataset_name": dataset.name,
                    "model": f"enhanced_{self.chat_model_name}",
                    "source": "mindsdb_enhanced_chat",
                    "response_time_seconds": response_time,
                    "user_id": user_id,
                    "session_id": session_id,
                    "organization_id": organization_id or dataset.organization_id
                })
                
                logger.info(f"✅ Successfully processed dataset chat in {response_time:.2f}s")
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

    def list_models(self) -> Dict[str, Any]:
        """List available models - using direct listing for reliability."""
        try:
            # For now, return the known models that we can create
            model_list = [
                {
                    "name": self.chat_model_name,
                    "status": "ready",
                    "engine": "google_gemini_engine",
                    "created_at": datetime.utcnow().isoformat()
                },
                {
                    "name": self.vision_model_name,
                    "status": "ready", 
                    "engine": "google_gemini_engine",
                    "created_at": datetime.utcnow().isoformat()
                }
            ]
            
            logger.info(f"✅ Listed {len(model_list)} available models")
            return {
                "data": model_list,
                "count": len(model_list),
                "timestamp": datetime.utcnow().isoformat()
            }
                
        except Exception as e:
            logger.error(f"❌ Model listing failed: {e}")
            return {
                "error": str(e),
                "data": [],
                "count": 0,
                "timestamp": datetime.utcnow().isoformat()
            }

    def delete_dataset_models(self, dataset_id: int) -> Dict[str, Any]:
        """Delete all models associated with a dataset including Gemini predictors."""
        try:
            if not self._ensure_connection():
                logger.warning(f"No connection available for deleting models for dataset {dataset_id}")
                return {"status": "warning", "message": "No connection available"}

            # List of model patterns to delete
            model_patterns = [
                f"dataset_{dataset_id}_chat",
                f"dataset_{dataset_id}_predictor", 
                f"dataset_{dataset_id}_gemini",
                f"dataset_{dataset_id}_vision",
                f"dataset_{dataset_id}_embedding",
                f"gemini_dataset_{dataset_id}",
                f"predictor_dataset_{dataset_id}"
            ]
            
            deleted_models = []
            failed_models = []
            
            for model_name in model_patterns:
                try:
                    # Use raw SQL to drop the model
                    drop_sql = f"DROP MODEL IF EXISTS mindsdb.{model_name};"
                    self.connection.query(drop_sql)
                    deleted_models.append(model_name)
                    logger.info(f"✅ Deleted model: {model_name}")
                except Exception as e:
                    failed_models.append(f"{model_name}: {str(e)}")
                    logger.warning(f"Model deletion failed for {model_name}: {e}")
            
            # Also try to delete any models that contain the dataset_id in their name
            try:
                # Get list of all models
                models_query = "SELECT name FROM mindsdb.models WHERE name LIKE '%dataset_%';"
                result = self.connection.query(models_query)
                
                if result and hasattr(result, 'fetch'):
                    models_data = result.fetch()
                    for row in models_data:
                        model_name = row.get('name', '')
                        if f"dataset_{dataset_id}" in model_name and model_name not in deleted_models:
                            try:
                                drop_sql = f"DROP MODEL IF EXISTS mindsdb.{model_name};"
                                self.connection.query(drop_sql)
                                deleted_models.append(model_name)
                                logger.info(f"✅ Deleted additional model: {model_name}")
                            except Exception as e:
                                failed_models.append(f"{model_name}: {str(e)}")
                                logger.warning(f"Additional model deletion failed for {model_name}: {e}")
            except Exception as e:
                logger.warning(f"Could not query for additional models: {e}")
            
            return {
                "status": "success" if deleted_models else "warning",
                "message": f"Deleted {len(deleted_models)} models",
                "deleted_models": deleted_models,
                "failed_models": failed_models
            }
            
        except Exception as e:
            logger.error(f"❌ Model deletion failed for dataset {dataset_id}: {e}")
            return {"status": "error", "message": str(e)}

    def get_databases(self) -> List[Dict[str, Any]]:
        """Get list of all database connections in MindsDB."""
        try:
            if not self._ensure_connection():
                logger.error("❌ Cannot connect to MindsDB to fetch databases")
                return []
            
            # Query to get all databases
            databases_query = "SHOW DATABASES"
            
            try:
                result = self.connection.query(databases_query)
                df = result.fetch()
                
                databases = []
                if not df.empty:
                    for _, row in df.iterrows():
                        # MindsDB returns database info in different formats
                        # Handle both 'Database' and 'database' column names
                        db_name = row.get('Database') or row.get('database') or row.get('name')
                        if db_name:
                            databases.append({
                                "name": str(db_name),
                                "type": "database",
                                "status": "active"
                            })
                
                logger.info(f"✅ Retrieved {len(databases)} databases from MindsDB")
                return databases
                
            except Exception as e:
                logger.error(f"❌ Failed to execute SHOW DATABASES query: {e}")
                # Return default databases that should exist in MindsDB
                return [
                    {"name": "mindsdb", "type": "system", "status": "active"},
                    {"name": "information_schema", "type": "system", "status": "active"}
                ]
                
        except Exception as e:
            logger.error(f"❌ Failed to get databases: {e}")
            return []
    
    def create_database_connection(self, db_name: str, engine: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new database connection in MindsDB."""
        try:
            if not self._ensure_connection():
                return {"status": "error", "message": "Cannot connect to MindsDB"}
            
            # Build CREATE DATABASE SQL
            params_json = json.dumps(parameters)
            create_db_sql = f"""
            CREATE DATABASE IF NOT EXISTS {db_name}
            WITH ENGINE = '{engine}',
            PARAMETERS = {params_json}
            """
            
            try:
                self.connection.query(create_db_sql)
                logger.info(f"✅ Created database connection: {db_name}")
                return {
                    "status": "success",
                    "message": f"Database {db_name} created successfully",
                    "database_name": db_name,
                    "engine": engine
                }
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"✅ Database {db_name} already exists")
                    return {
                        "status": "exists",
                        "message": f"Database {db_name} already exists",
                        "database_name": db_name,
                        "engine": engine
                    }
                else:
                    raise e
                    
        except Exception as e:
            logger.error(f"❌ Failed to create database connection {db_name}: {e}")
            return {
                "status": "error",
                "message": f"Failed to create database: {str(e)}",
                "database_name": db_name
            }
    
    def execute_query(self, query: str, connection_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a query - alias for execute_sql for compatibility."""
        return self.execute_sql(query)

    def execute_sql(self, query: str) -> Dict[str, Any]:
        """Execute a custom SQL query."""
        try:
            if not self._ensure_connection():
                return {"status": "error", "message": "Cannot connect to MindsDB"}
            
            try:
                result = self.connection.query(query)
                df = result.fetch()
                
                # Convert DataFrame to list of dictionaries
                rows = df.to_dict('records') if not df.empty else []
                
                logger.info(f"✅ Executed SQL query, returned {len(rows)} rows")
                return {
                    "status": "success",
                    "rows": rows,
                    "row_count": len(rows),
                    "query": query
                }
                
            except Exception as e:
                logger.error(f"❌ SQL execution failed: {e}")
                return {
                    "status": "error",
                    "message": f"SQL execution failed: {str(e)}",
                    "query": query
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to execute SQL: {e}")
            return {
                "status": "error",
                "message": f"Failed to execute SQL: {str(e)}",
                "query": query
            }

    def initialize_gemini_integration(self) -> Dict[str, Any]:
        """Initialize complete Gemini integration."""
        logger.info("🚀 Initializing Gemini integration")
        
        components = {}
        overall_success = True
        
        try:
            # Test basic connection
            health = self.health_check()
            components["connection"] = {
                "status": "success" if health.get("status") != "error" else "error",
                "details": health
            }
            if health.get("status") == "error":
                overall_success = False
            
            # Create/verify engine
            engine_result = self.create_gemini_engine()
            components["engine"] = {
                "status": "success" if engine_result.get("status") != "error" else "error",
                "details": engine_result
            }
            if engine_result.get("status") == "error":
                overall_success = False
            
            # Create default chat model
            model_result = self.create_gemini_model(self.chat_model_name)
            components["default_model"] = {
                "status": "success" if model_result.get("status") != "error" else "error",
                "details": model_result
            }
            if model_result.get("status") == "error":
                overall_success = False
                
            # Test basic chat
            if overall_success:
                try:
                    chat_result = self.ai_chat("Hello, can you respond?")
                    if chat_result.get("answer"):
                        components["chat_test"] = {"status": "success", "details": "Chat functional"}
                    else:
                        components["chat_test"] = {"status": "error", "details": "No chat response"}
                        overall_success = False
                except Exception as e:
                    components["chat_test"] = {"status": "error", "details": str(e)}
                    overall_success = False
            
            result = {
                "overall_status": "success" if overall_success else "partial",
                "components": components,
                "configuration": {
                    "engine_name": self.engine_name,
                    "default_model": self.default_model,
                    "api_key_configured": bool(self.api_key),
                    "connection_status": "connected" if self._connected else "disconnected"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if overall_success:
                logger.info("🚀 Gemini integration initialization successful")
            else:
                logger.warning("⚠️ Gemini integration initialization partial")
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Gemini integration initialization failed: {e}")
            return {
                "overall_status": "error",
                "error": str(e),
                "components": components,
                "timestamp": datetime.utcnow().isoformat()
            }


# Create service instance
mindsdb_service = MindsDBService()