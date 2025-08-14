import secrets
from typing import List, Optional, Dict, Any
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    PROJECT_NAME: str = "AI Share Platform"
    VERSION: str = "1.0.0"
    
    # Database - Single unified database location
    DATABASE_URL: str = "sqlite:///../storage/aishare_platform.db"
    
    # CORS origins - will be parsed from comma-separated string
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:10103,http://localhost:3001,http://localhost:3004"
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]
        return self.BACKEND_CORS_ORIGINS
    
    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Google API Configuration - Now from environment
    GOOGLE_API_KEY: Optional[str] = None
    
    # MindsDB Configuration
    MINDSDB_URL: str = "http://127.0.0.1:47334"
    MINDSDB_DATABASE: str = "mindsdb"
    MINDSDB_USERNAME: Optional[str] = None
    MINDSDB_PASSWORD: Optional[str] = None
    
    # AI Model Configuration - From environment
    DEFAULT_GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_ENGINE_NAME: str = "google_gemini_engine"
    GEMINI_CHAT_MODEL_NAME: str = "gemini_chat_assistant"
    GEMINI_VISION_MODEL_NAME: str = "gemini_vision_assistant"
    GEMINI_EMBEDDING_MODEL_NAME: str = "gemini_embedding_assistant"
    
    # Data Sharing Configuration
    ENABLE_DATA_SHARING: bool = True
    ENABLE_AI_CHAT: bool = True
    SHARE_LINK_EXPIRY_HOURS: int = 24
    MAX_CHAT_SESSIONS_PER_DATASET: int = 10
    
    # S3 Configuration (optional)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_DEFAULT_REGION: str = "us-east-1"
    S3_BUCKET_NAME: Optional[str] = None
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_FILE_TYPES: str = "csv,json,xlsx,xls,txt,pdf,docx,doc,rtf,odt"
    UPLOAD_PATH: str = "./storage/uploads"
    
    # Document Processing Configuration
    MAX_DOCUMENT_SIZE_MB: int = 50
    SUPPORTED_DOCUMENT_TYPES: str = "pdf,docx,doc,txt,rtf,odt"
    DOCUMENT_STORAGE_PATH: str = "./storage/documents"
    
    # PDF Processing Configuration
    ENABLE_PDF_PROCESSING: bool = True
    PDF_PREVIEW_MAX_WIDTH: int = 400
    PDF_TEXT_EXTRACTION_MAX_PAGES: int = 10
    PDF_PROCESSING_LIBRARIES: str = "PyPDF2,PyMuPDF"  # Required libraries for PDF processing
    
    # Data Connector Configuration
    CONNECTOR_TIMEOUT: int = 30
    MAX_CONNECTORS_PER_ORG: int = 10
    ENABLE_S3_CONNECTOR: bool = True
    ENABLE_DATABASE_CONNECTORS: bool = True
    
    # SSL Configuration for Development
    DISABLE_SSL_FOR_LOCALHOST: bool = True
    FORCE_SSL_IN_PRODUCTION: bool = True
    SSL_DEVELOPMENT_MODE: bool = True  # Automatically disable SSL for localhost in development
    
    def get_allowed_file_types(self) -> List[str]:
        """Parse allowed file types from comma-separated string."""
        return [ext.strip() for ext in self.ALLOWED_FILE_TYPES.split(",") if ext.strip()]
    
    def should_disable_ssl_for_host(self, host: str, port: Optional[int] = None) -> bool:
        """
        Determine if SSL should be disabled for a specific host/port combination
        
        Args:
            host: Hostname or IP address
            port: Optional port number
            
        Returns:
            bool: True if SSL should be disabled
        """
        if not self.SSL_DEVELOPMENT_MODE:
            return False
            
        # Import here to avoid circular imports
        from app.utils.environment import EnvironmentDetector
        
        return EnvironmentDetector.should_disable_ssl(host, port)
    
    def get_ssl_config_for_connector(self, connector_type: str, host: str, 
                                   port: Optional[int] = None, 
                                   existing_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get SSL configuration for a connector based on environment and host
        
        Args:
            connector_type: Type of connector (mysql, postgresql, etc.)
            host: Hostname or IP address  
            port: Optional port number
            existing_config: Existing configuration to merge
            
        Returns:
            Dict containing SSL configuration
        """
        if not self.SSL_DEVELOPMENT_MODE:
            return existing_config or {}
            
        # Import here to avoid circular imports
        from app.utils.environment import EnvironmentDetector
        
        return EnvironmentDetector.get_ssl_config_for_connection(
            connector_type, host, port, existing_config
        )
    
    # Admin user
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str
    
    class Config:
        env_file = ".env"  # Use local .env file in backend directory
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()