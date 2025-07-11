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

            # Create model using raw SQL
            create_model_sql = f"""
            CREATE MODEL IF NOT EXISTS mindsdb.{model_name}
            PREDICT answer
            USING
                engine = '{self.engine_name}',
                column = '{column_name}',
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
        """Handle AI chat using direct Gemini API as primary method."""
        if not model_name:
            model_name = self.chat_model_name

        try:
            # Use direct Gemini as primary method since it's reliable and what user wants
            logger.info(f"💬 Using direct Gemini API for chat (model: {model_name})")
            result = self._direct_gemini_chat(message)
            
            # Update the model name to reflect the requested model
            result["model"] = f"{model_name} (Direct Gemini API)"
            result["source"] = "direct_gemini_primary"
            
            return result

        except Exception as e:
            logger.error(f"❌ AI chat failed: {e}")
            return {
                "error": f"Chat failed: {str(e)}",
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }

    def _direct_gemini_chat(self, message: str) -> Dict[str, Any]:
        """Direct Gemini API chat as fallback."""
        try:
            model = genai.GenerativeModel(self.default_model)
            response = model.generate_content(message)
            
            return {
                "answer": response.text,
                "model": f"{self.default_model} (Direct API)",
                "timestamp": datetime.utcnow().isoformat(),
                "tokens_used": len(message.split()) + len(response.text.split()),
                "source": "direct_gemini"
            }
        except Exception as e:
            logger.error(f"❌ Direct Gemini API failed: {e}")
            return {
                "error": f"Direct API failed: {str(e)}",
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
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
            
            self.connection.query(create_model_sql)
            logger.info(f"✅ Created enhanced {dataset_type} model: {model_name}")
            
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
        """Chat with dataset using direct Gemini with enhanced dataset context."""
        try:
            from app.core.database import get_db
            from app.models.dataset import Dataset
            from sqlalchemy.orm import Session
            import time
            start_time = time.time()
            
            # Get dataset information from database
            db = next(get_db())
            dataset = db.query(Dataset).filter(Dataset.id == int(dataset_id)).first()
            
            dataset_context = ""
            if dataset:
                dataset_context = f"""
                Dataset Information:
                - Name: {dataset.name}
                - Type: {dataset.type}
                - Description: {dataset.description or 'No description available'}
                - Rows: {dataset.row_count or 'Unknown'}
                - Columns: {dataset.column_count or 'Unknown'}
                - Size: {dataset.size_bytes or 'Unknown'} bytes
                - Created: {dataset.created_at}
                """
                
                # Add file content context for small files
                if dataset.source_url and dataset.type.upper() in ["CSV", "JSON", "PDF"]:
                    try:
                        content_result = self.process_file_content(dataset.source_url, dataset.type)
                        if content_result.get("success"):
                            # Include a sample of the content for context
                            content = content_result["content"]
                            if len(content) > 2000:  # Limit content size
                                content = content[:2000] + "... [content truncated]"
                            dataset_context += f"\n\nDataset Content Sample:\n{content}"
                            
                            # Add metadata
                            if content_result.get("metadata"):
                                metadata = content_result["metadata"]
                                dataset_context += f"\n\nFile Metadata: {metadata}"
                    except Exception as e:
                        logger.warning(f"Could not load dataset content: {e}")
            
            # Enhanced prompt with actual dataset context
            enhanced_message = f"""
            You are analyzing a specific dataset. Here is the detailed information about this dataset:
            
            {dataset_context}
            
            User Question: {message}
            
            Instructions:
            1. Use the actual dataset information provided above to answer questions
            2. Reference specific data points, column names, and values when available
            3. If the user asks about data that isn't visible in the sample, explain what you can see and suggest what analysis might be helpful
            4. Be specific and analytical, using the actual dataset structure and content
            5. If performing calculations, use the actual data shown
            6. Mention specific values, patterns, or insights from the actual dataset content
            
            Please provide a detailed, data-driven response based on this specific dataset.
            """
            
            logger.info(f"💬 Enhanced dataset chat for dataset {dataset_id} with content context")
            result = self._direct_gemini_chat(enhanced_message)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Add dataset context to the response
            result["dataset_id"] = dataset_id
            result["dataset_name"] = dataset.name if dataset else "Unknown"
            result["model"] = f"Dataset Content Analyzer (Gemini)"
            result["source"] = "dataset_content_gemini"
            result["has_content_context"] = bool(dataset_context)
            result["response_time_seconds"] = response_time
            result["user_id"] = user_id
            result["session_id"] = session_id
            result["organization_id"] = organization_id or (dataset.organization_id if dataset else None)
            
            # Log chat interaction asynchronously
            try:
                import asyncio
                from app.services.analytics import analytics_service
                asyncio.create_task(analytics_service.log_chat_interaction(
                    dataset_id=int(dataset_id),
                    user_message=message,
                    ai_response=result.get("answer", ""),
                    user_id=user_id,
                    session_id=session_id,
                    llm_provider="gemini",
                    llm_model=self.chat_model_name,
                    response_time_seconds=response_time,
                    organization_id=organization_id or (dataset.organization_id if dataset else None),
                    success=bool(result.get("answer"))
                ))
            except Exception as e:
                logger.warning(f"Failed to log chat interaction: {e}")
            
            return result

        except Exception as e:
            logger.error(f"❌ Enhanced dataset chat failed: {e}")
            return {
                "error": f"Dataset chat failed: {str(e)}",
                "dataset_id": dataset_id,
                "message": message,
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
        """Delete models associated with a dataset using raw SQL."""
        try:
            model_name = f"dataset_{dataset_id}_chat"
            
            if not self._ensure_connection():
                logger.warning(f"No connection available for deleting {model_name}")
                return {"status": "warning", "message": "No connection available"}

            # Use raw SQL to drop the model
            drop_sql = f"DROP MODEL IF EXISTS mindsdb.{model_name};"
            
            try:
                self.connection.query(drop_sql)
                logger.info(f"✅ Deleted model: {model_name}")
                return {"status": "success", "message": f"Model {model_name} deleted"}
            except Exception as e:
                logger.warning(f"Model deletion failed (may not exist): {e}")
                return {"status": "warning", "message": f"Model may not exist: {e}"}
            
        except Exception as e:
            logger.error(f"❌ Model deletion failed: {e}")
            return {"status": "error", "message": str(e)}

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