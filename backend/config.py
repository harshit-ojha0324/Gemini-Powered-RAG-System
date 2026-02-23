from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Google Gemini (optional for testing; will use fallback if not provided)
    gemini_api_key: Optional[str] = None
    gemini_model: str = "models/embedding-001"
    
    # Storage
    chroma_persist_directory: str = "./data/vectorstore"
    documents_directory: str = "./data/documents"
    logs_directory: str = "./data/logs"
    
    # Limits
    max_file_size_mb: int = 10
    allowed_extensions: str = "pdf"
    max_chunks_per_document: int = 100
    
    # Security
    enable_pii_detection: bool = True
    enable_injection_detection: bool = True
    enable_content_filtering: bool = True
    log_security_events: bool = True
    
    # Server
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()