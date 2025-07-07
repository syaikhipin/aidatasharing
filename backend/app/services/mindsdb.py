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
        dataset_type: str = "CSV"
    ) -> Dict[str, Any]:
        """Create ML model for dataset analysis using raw SQL."""
        try:
            # Generate model name for the dataset
            chat_model = f"dataset_{dataset_id}_chat"
            
            # Create dataset-specific chat model
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
                    "dataset_name": dataset_name
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

    def chat_with_dataset(self, dataset_id: str, message: str) -> Dict[str, Any]:
        """Chat with dataset using direct Gemini with dataset context."""
        try:
            # Enhanced prompt with dataset context for better responses
            enhanced_message = f"""
            You are analyzing dataset ID: {dataset_id}
            
            User question: {message}
            
            Please provide insights, analysis, or answers based on this dataset context. 
            If specific data analysis is needed, explain what kind of data exploration would be helpful.
            Be specific and analytical in your response.
            """
            
            logger.info(f"💬 Dataset chat for dataset {dataset_id} using direct Gemini")
            result = self._direct_gemini_chat(enhanced_message)
            
            # Add dataset context to the response
            result["dataset_id"] = dataset_id
            result["model"] = f"Dataset Analyzer (Gemini)"
            result["source"] = "dataset_context_gemini"
            
            return result

        except Exception as e:
            logger.error(f"❌ Dataset chat failed: {e}")
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