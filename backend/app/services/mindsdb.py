import requests
from typing import Dict, List, Optional, Any
from app.core.config import settings
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class MindsDBService:
    def __init__(self):
        # Use settings from environment
        self.base_url = settings.MINDSDB_URL
        self.database = settings.MINDSDB_DATABASE
        self.api_key = settings.GOOGLE_API_KEY
        
        # Model configurations from environment
        self.engine_name = settings.GEMINI_ENGINE_NAME
        self.default_model = settings.DEFAULT_GEMINI_MODEL
        self.chat_model_name = settings.GEMINI_CHAT_MODEL_NAME
        self.vision_model_name = settings.GEMINI_VISION_MODEL_NAME
        self.embedding_model_name = settings.GEMINI_EMBEDDING_MODEL_NAME
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        # Add authentication if available
        if settings.MINDSDB_USERNAME and settings.MINDSDB_PASSWORD:
            self.session.auth = (settings.MINDSDB_USERNAME, settings.MINDSDB_PASSWORD)

    def _is_mindsdb_available(self) -> bool:
        """Check if MindsDB is available."""
        try:
            response = self.session.get(f"{self.base_url}/api/status", timeout=5)
            return response.status_code == 200
        except:
            return False

    def _direct_gemini_chat(self, message: str) -> Dict[str, Any]:
        """Direct Gemini API call when MindsDB is not available."""
        if not self.api_key:
            raise Exception("Google API key not configured")
            
        try:
            # Direct call to Google Gemini API
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.default_model}:generateContent"
            
            headers = {
                'Content-Type': 'application/json',
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": message
                    }]
                }]
            }
            
            response = requests.post(
                f"{gemini_url}?key={self.api_key}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('candidates') and len(result['candidates']) > 0:
                    content = result['candidates'][0].get('content', {})
                    if content.get('parts') and len(content['parts']) > 0:
                        answer = content['parts'][0].get('text', 'No response generated')
                        return {
                            "answer": answer,
                            "model": f"{self.default_model} (Direct API)",
                            "timestamp": datetime.utcnow().isoformat(),
                            "tokens_used": len(message.split()) + len(answer.split()) if answer else 0,
                            "source": "direct_gemini"
                        }
            
            return {
                "answer": "I'm sorry, I couldn't generate a response using the direct API.",
                "model": f"{self.default_model} (Direct API)",
                "timestamp": datetime.utcnow().isoformat(),
                "tokens_used": 0,
                "source": "direct_gemini",
                "error": True
            }
            
        except Exception as e:
            logger.error(f"Direct Gemini API failed: {e}")
            return {
                "answer": f"Direct API Error: {str(e)}",
                "model": f"{self.default_model} (Direct API)",
                "timestamp": datetime.utcnow().isoformat(),
                "tokens_used": 0,
                "source": "direct_gemini",
                "error": True
            }

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a SQL query against MindsDB."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/sql/query",
                json={"query": query}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"MindsDB query failed: {e}")
            raise Exception(f"MindsDB query failed: {str(e)}")

    def create_gemini_engine(self) -> Dict[str, Any]:
        """Create Google Gemini ML engine."""
        if not self.api_key:
            raise Exception("Google API key not configured")
        
        # Check if engine already exists
        try:
            check_query = f"SHOW ML_ENGINES WHERE name = '{self.engine_name}';"
            result = self.execute_query(check_query)
            if result.get('data') and len(result['data']) > 0:
                logger.info(f"Engine {self.engine_name} already exists, skipping creation")
                return {"message": f"Engine {self.engine_name} already exists", "status": "exists"}
        except Exception as e:
            logger.warning(f"Could not check engine existence: {e}")
            
        # Create the engine
        query = f"""
        CREATE ML_ENGINE {self.engine_name}
        FROM google_gemini
        USING
          api_key = '{self.api_key}';
        """
        try:
            return self.execute_query(query)
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"Engine {self.engine_name} already exists")
                return {"message": f"Engine {self.engine_name} already exists", "status": "exists"}
            else:
                raise e

    def create_gemini_model(
        self, 
        model_name: str, 
        model_type: str = "chat",
        prompt_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a Gemini model for various tasks."""
        if not self.api_key:
            raise Exception("Google API key not configured")
            
        # Ensure engine exists
        try:
            self.create_gemini_engine()
        except Exception as e:
            logger.warning(f"Engine creation warning: {e}")
        
        # Build the query based on model type
        if model_type == "chat":
            # Use a default prompt template if none provided
            if not prompt_template:
                prompt_template = "You are a helpful AI assistant. Answer the following question: {{question}}"
            # Escape single quotes in prompt template
            safe_prompt_template = prompt_template.replace("'", "''")
            using_clause = f"engine = '{self.engine_name}', model_name = '{self.default_model}', prompt_template = '{safe_prompt_template}'"
        elif model_type == "vision":
            using_clause = f"engine = '{self.engine_name}', model_name = 'gemini-2.0-flash', prompt_template = 'Analyze this image and answer: {{question}}'"
        elif model_type == "embedding":
            using_clause = f"engine = '{self.engine_name}', model_name = 'text-embedding-004'"
        else:
            using_clause = f"engine = '{self.engine_name}', model_name = '{self.default_model}', prompt_template = 'Answer the question: {{question}}'"
        
        # Check if model already exists
        try:
            check_query = f"SHOW MODELS WHERE name = '{model_name}';"
            result = self.execute_query(check_query)
            if result.get('data') and len(result['data']) > 0:
                logger.info(f"Model {model_name} already exists, skipping creation")
                return {"message": f"Model {model_name} already exists", "status": "exists"}
        except Exception as e:
            logger.warning(f"Could not check model existence: {e}")
        
        query = f"""
        CREATE MODEL {model_name}
        PREDICT response
        USING
          {using_clause};
        """
        try:
            return self.execute_query(query)
        except Exception as e:
            if "already exists" in str(e).lower() or "exists" in str(e).lower():
                logger.info(f"Model {model_name} already exists")
                return {"message": f"Model {model_name} already exists", "status": "exists"}
            else:
                raise e

    def ai_chat(self, message: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Send a message to Gemini AI for chat response."""
        # Check if MindsDB is available
        if not self._is_mindsdb_available():
            logger.info("MindsDB not available, using direct Gemini API")
            return self._direct_gemini_chat(message)
        
        try:
            chat_model = model_name or self.chat_model_name
            
            # Ensure chat model exists
            try:
                self.create_gemini_model(chat_model, "chat")
            except Exception as e:
                logger.warning(f"Model creation warning: {e}")
            
            # Query the model (use response column like dataset models)
            query = f"""
            SELECT response
            FROM {chat_model}
            WHERE question = '{message.replace("'", "''")}';
            """
            
            result = self.execute_query(query)
            
            # Extract answer from result
            if result.get('data') and len(result['data']) > 0:
                # Handle both list and dict responses
                row = result['data'][0]
                if isinstance(row, list) and len(row) > 0:
                    answer = row[0]
                elif isinstance(row, dict):
                    answer = row.get('response', row.get('answer', 'No response generated'))
                else:
                    answer = str(row)
                return {
                    "answer": answer,
                    "model": chat_model,
                    "timestamp": datetime.utcnow().isoformat(),
                    "tokens_used": len(message.split()) + len(answer.split()) if answer else 0,
                    "source": "mindsdb"
                }
            else:
                return {
                    "answer": "I'm sorry, I couldn't generate a response.",
                    "model": chat_model,
                    "timestamp": datetime.utcnow().isoformat(),
                    "tokens_used": 0,
                    "source": "mindsdb"
                }
                
        except Exception as e:
            logger.error(f"MindsDB AI chat failed, falling back to direct API: {e}")
            return self._direct_gemini_chat(message)

    def natural_language_to_sql(self, question: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Convert natural language to SQL using Gemini."""
        try:
            # Create enhanced prompt for SQL generation
            prompt = f"Convert this natural language question to SQL: {question}"
            if context:
                prompt = f"Given this database context: {context}\n\n{prompt}"
            
            response = self.ai_chat(prompt, self.chat_model_name)
            
            # Extract SQL from response
            answer = response.get("answer", "")
            
            return {
                "sql_query": answer,
                "original_question": question,
                "confidence": 0.8 if "SELECT" in answer.upper() else 0.3,
                "model": self.chat_model_name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Natural language to SQL failed: {e}")
            return {
                "sql_query": "",
                "original_question": question,
                "confidence": 0.0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def query_gemini_model(self, model_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Query a specific Gemini model."""
        try:
            # Build WHERE clause from input data
            where_conditions = []
            for key, value in input_data.items():
                if isinstance(value, str):
                    escaped_value = value.replace("'", "''")
                    where_conditions.append(f"{key} = '{escaped_value}'")
                else:
                    where_conditions.append(f"{key} = {value}")
            
            where_clause = " AND ".join(where_conditions)
            
            query = f"""
            SELECT *
            FROM {model_name}
            WHERE {where_clause};
            """
            
            return self.execute_query(query)
            
        except Exception as e:
            logger.error(f"Model query failed: {e}")
            raise Exception(f"Model query failed: {str(e)}")

    def create_vision_model(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a vision model for image analysis."""
        vision_model = model_name or self.vision_model_name
        return self.create_gemini_model(vision_model, "vision")

    def create_embedding_model(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Create an embedding model for semantic search."""
        embedding_model = model_name or self.embedding_model_name
        return self.create_gemini_model(embedding_model, "embedding")

    def get_engine_status(self) -> Dict[str, Any]:
        """Get the status of the Gemini engine."""
        try:
            query = f"SHOW ML_ENGINES WHERE name = '{self.engine_name}';"
            result = self.execute_query(query)
            
            return {
                "engine_name": self.engine_name,
                "exists": bool(result.get('data')),
                "status": "active" if result.get('data') else "not_found",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Engine status check failed: {e}")
            return {
                "engine_name": self.engine_name,
                "exists": False,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def initialize_gemini_integration(self) -> Dict[str, Any]:
        """Initialize complete Gemini integration."""
        try:
            results = {}
            
            # Create engine
            try:
                engine_result = self.create_gemini_engine()
                results["engine"] = {"status": "success", "result": engine_result}
            except Exception as e:
                results["engine"] = {"status": "error", "error": str(e)}
            
            # Create chat model
            try:
                chat_result = self.create_gemini_model(self.chat_model_name, "chat")
                results["chat_model"] = {"status": "success", "result": chat_result}
            except Exception as e:
                results["chat_model"] = {"status": "error", "error": str(e)}
            
            # Create vision model
            try:
                vision_result = self.create_vision_model()
                results["vision_model"] = {"status": "success", "result": vision_result}
            except Exception as e:
                results["vision_model"] = {"status": "error", "error": str(e)}
            
            # Create embedding model
            try:
                embedding_result = self.create_embedding_model()
                results["embedding_model"] = {"status": "success", "result": embedding_result}
            except Exception as e:
                results["embedding_model"] = {"status": "error", "error": str(e)}
            
            # Test chat functionality
            try:
                test_response = self.ai_chat("Hello, this is a test message.")
                results["chat_test"] = {"status": "success", "response": test_response}
            except Exception as e:
                results["chat_test"] = {"status": "error", "error": str(e)}
            
            return {
                "overall_status": "success",
                "timestamp": datetime.utcnow().isoformat(),
                "components": results,
                "configuration": {
                    "engine_name": self.engine_name,
                    "default_model": self.default_model,
                    "chat_model": self.chat_model_name,
                    "vision_model": self.vision_model_name,
                    "embedding_model": self.embedding_model_name,
                    "api_key_configured": bool(self.api_key)
                }
            }
            
        except Exception as e:
            logger.error(f"Gemini integration initialization failed: {e}")
            return {
                "overall_status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def list_models(self) -> Dict[str, Any]:
        """List all available models."""
        try:
            query = "SHOW MODELS;"
            return self.execute_query(query)
        except Exception as e:
            logger.error(f"List models failed: {e}")
            return {"error": str(e), "data": []}

    def check_health(self) -> Dict[str, Any]:
        """Check MindsDB service health."""
        mindsdb_available = self._is_mindsdb_available()
        
        health_status = {
            "mindsdb_available": mindsdb_available,
            "mindsdb_url": self.base_url,
            "api_key_configured": bool(self.api_key),
            "direct_gemini_available": bool(self.api_key),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if mindsdb_available:
            health_status["status"] = "healthy"
            health_status["connected"] = True
        elif self.api_key:
            health_status["status"] = "healthy_fallback"
            health_status["connected"] = False
            health_status["message"] = "MindsDB unavailable, using direct Gemini API"
        else:
            health_status["status"] = "error"
            health_status["connected"] = False
            health_status["error"] = "MindsDB unavailable and no Google API key configured"
            
        return health_status

    def create_dataset_ml_model(
        self, 
        dataset_id: int, 
        dataset_name: str, 
        dataset_type: str = "CSV",
        user_id: int = None
    ) -> Dict[str, Any]:
        """Create a specialized ML model for a specific dataset."""
        try:
            # Generate unique model name based on dataset
            model_name = f"dataset_{dataset_id}_chat_model"
            
            # Use default engine to avoid conflicts
            engine_name = self.engine_name
            
            # Ensure default engine exists
            try:
                self.create_gemini_engine()
            except Exception as e:
                logger.warning(f"Engine creation warning: {e}")
            
            # Check if model already exists
            try:
                check_query = f"SHOW MODELS WHERE name = '{model_name}';"
                result = self.execute_query(check_query)
                if result.get('data') and len(result['data']) > 0:
                    logger.info(f"Dataset model {model_name} already exists")
                    return {
                        "success": True,
                        "chat_model": model_name,
                        "engine": engine_name,
                        "dataset_id": dataset_id,
                        "message": f"ML model already exists for dataset: {dataset_name}",
                        "note": "Using existing model"
                    }
            except Exception as e:
                logger.warning(f"Could not check model existence: {e}")
            
            # Create a simpler, more reliable ML model with proper prompt template
            # Escape single quotes in dataset name to prevent SQL syntax errors
            safe_dataset_name = dataset_name.replace("'", "''")
            prompt_template = f"You are an AI assistant helping users understand and analyze the dataset {safe_dataset_name}. Answer the following question about this dataset: {{{{question}}}}"
            
            model_query = f"""
            CREATE MODEL {model_name}
            PREDICT response
            USING
                engine = '{engine_name}',
                model_name = '{self.default_model}',
                prompt_template = '{prompt_template}',
                max_tokens = 1000;
            """
            
            result = self.execute_query(model_query)
            
            # Wait a moment for model to initialize
            import time
            time.sleep(2)
            
            return {
                "success": True,
                "chat_model": model_name,
                "engine": engine_name,
                "dataset_id": dataset_id,
                "message": f"ML model created successfully for dataset: {dataset_name}",
                "model_result": result,
                "note": "Model may take a few moments to be ready for use"
            }
            
        except Exception as e:
            logger.error(f"Failed to create ML model for dataset {dataset_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "dataset_id": dataset_id,
                "message": f"Failed to create ML model for dataset: {dataset_name}"
            }
    
    def _generate_dataset_prompt_template(self, dataset_name: str, dataset_type: str) -> str:
        """Generate a specialized prompt template for the dataset."""
        base_template = f"""You are an AI assistant specialized in analyzing and discussing the dataset "{dataset_name}".

Dataset Information:
- Name: {dataset_name}
- Type: {dataset_type}
- You have access to this dataset and can answer questions about its content, structure, and insights.

When answering questions:
1. Be specific about this dataset
2. Provide data-driven insights when possible
3. Explain any patterns or trends you observe
4. Suggest relevant analyses or visualizations
5. Be helpful and informative

User Question: {{{{question}}}}

Please provide a comprehensive answer about this dataset:"""
        
        return base_template.replace("'", "''")  # Escape single quotes for SQL
    
    def chat_with_dataset(
        self, 
        dataset_id: int, 
        message: str, 
        model_type: str = "chat"
    ) -> Dict[str, Any]:
        """Chat specifically about a dataset using its dedicated model."""
        try:
            model_name = f"dataset_{dataset_id}_chat_model"
            
            # First check if model exists and is ready
            model_status = self._check_model_status(model_name)
            
            if not model_status.get("exists"):
                # Model doesn't exist, try to use general chat
                logger.warning(f"Dataset model {model_name} doesn't exist, using general chat")
                return self._fallback_to_general_chat(dataset_id, message)
            
            if model_status.get("status") != "complete":
                # Model is not ready, try to use general chat
                logger.warning(f"Dataset model {model_name} not ready (status: {model_status.get('status')}), using general chat")
                return self._fallback_to_general_chat(dataset_id, message)
            
            # Query the dataset-specific model
            query = f"""
            SELECT response
            FROM {model_name}
            WHERE question = '{message.replace("'", "''")}';
            """
            
            logger.info(f"Executing query for dataset {dataset_id}: {query}")
            
            result = self.execute_query(query)
            logger.info(f"Query result for dataset {dataset_id}: {result}")
            
            # Extract answer from result
            if result.get('data') and len(result['data']) > 0:
                # Try different ways to extract the response
                row = result['data'][0]
                if isinstance(row, list) and len(row) > 0:
                    answer = row[0]
                elif isinstance(row, dict):
                    answer = row.get('response', row.get('answer', 'No response generated'))
                else:
                    answer = str(row)
                
                logger.info(f"Extracted answer: {answer[:100]}...")
                
                return {
                    "answer": answer,
                    "model": model_name,
                    "dataset_id": dataset_id,
                    "model_type": model_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "tokens_used": len(message.split()) + len(answer.split()) if answer else 0,
                    "source": "mindsdb_dataset_model"
                }
            else:
                # No data returned, fallback to general chat
                logger.warning(f"No data returned from {model_name}, using fallback")
                return self._fallback_to_general_chat(dataset_id, message)
                
        except Exception as e:
            logger.error(f"Dataset chat failed for dataset {dataset_id}: {e}")
            # Fallback to general chat on error
            return self._fallback_to_general_chat(dataset_id, message)
    
    def _check_model_status(self, model_name: str) -> Dict[str, Any]:
        """Check if a model exists and its status."""
        try:
            query = f"SHOW MODELS WHERE name = '{model_name}';"
            result = self.execute_query(query)
            
            if result.get('data') and len(result['data']) > 0:
                model_data = result['data'][0]
                status = model_data[5] if len(model_data) > 5 else "unknown"
                return {
                    "exists": True,
                    "status": status,
                    "data": model_data
                }
            else:
                return {"exists": False, "status": "not_found"}
                
        except Exception as e:
            logger.error(f"Error checking model status for {model_name}: {e}")
            return {"exists": False, "status": "error", "error": str(e)}
    
    def _fallback_to_general_chat(self, dataset_id: int, message: str) -> Dict[str, Any]:
        """Fallback to general AI chat when dataset-specific model is not available."""
        try:
            # Enhance the message with dataset context
            enhanced_message = f"I'm asking about dataset ID {dataset_id}. {message}"
            
            # Use the general AI chat function
            response = self.ai_chat(enhanced_message)
            
            # Add dataset context to the response
            response["dataset_id"] = dataset_id
            response["model_type"] = "fallback_general"
            response["note"] = "Used general AI model as dataset-specific model was not available"
            
            return response
            
        except Exception as e:
            logger.error(f"Fallback chat failed: {e}")
            return {
                "answer": f"I'm sorry, I'm having trouble processing your question about this dataset right now. Please try again later.",
                "model": "fallback_error",
                "dataset_id": dataset_id,
                "timestamp": datetime.utcnow().isoformat(),
                "tokens_used": 0,
                "source": "error_fallback",
                "error": True
            }
    
    def delete_dataset_models(self, dataset_id: int) -> Dict[str, Any]:
        """Delete ML models associated with a dataset."""
        try:
            model_name = f"dataset_{dataset_id}_chat_model"
            results = []
            
            # Delete the chat model
            try:
                query = f"DROP MODEL IF EXISTS {model_name};"
                result = self.execute_query(query)
                results.append(f"Deleted model: {model_name}")
            except Exception as e:
                results.append(f"Failed to delete model {model_name}: {e}")
            
            return {
                "success": True,
                "dataset_id": dataset_id,
                "message": "Dataset model cleanup completed",
                "details": results
            }
            
        except Exception as e:
            logger.error(f"Failed to delete models for dataset {dataset_id}: {e}")
            return {
                "success": False,
                "dataset_id": dataset_id,
                "error": str(e),
                "message": "Failed to cleanup dataset model"
            }


# Global instance
mindsdb_service = MindsDBService() 