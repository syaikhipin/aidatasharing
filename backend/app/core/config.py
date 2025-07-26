import secrets
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    PROJECT_NAME: str = "AI Share Platform"
    VERSION: str = "1.0.0"
    
    # Database - Unified database location
    DATABASE_URL: str = "sqlite:///./storage/aishare_platform.db"
    
    # CORS origins - will be parsed from comma-separated string
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,http://localhost:3001,http://localhost:3004"
    
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
    
    # Data Connector Configuration
    CONNECTOR_TIMEOUT: int = 30
    MAX_CONNECTORS_PER_ORG: int = 10
    ENABLE_S3_CONNECTOR: bool = True
    ENABLE_DATABASE_CONNECTORS: bool = True
    
    def get_allowed_file_types(self) -> List[str]:
        """Parse allowed file types from comma-separated string."""
        return [ext.strip() for ext in self.ALLOWED_FILE_TYPES.split(",") if ext.strip()]
    
    # Admin user
    FIRST_SUPERUSER: str = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "admin123"
    
    class Config:
        env_file = "../.env"  # Use unified .env file from project root
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()