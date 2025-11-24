"""
Application configuration using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    environment: str = "development"
    
    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: Optional[str] = None
    supabase_jwt_secret: Optional[str] = None
    
    # ChromaDB
    chromadb_host: str = "memory_store"
    chromadb_port: int = 8000
    
    # Redis
    redis_host: str = "cache_layer"
    redis_port: int = 6379
    
    # Langfuse (optional observability)
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "http://observer:3000"
    langfuse_base_url: Optional[str] = None  # Allow Langfuse Cloud URL if provided
    
    # AI Models
    google_api_key: str = ""
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    
    # E2B
    e2b_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env (like langfuse_base_url)


settings = Settings()


settings = Settings()

