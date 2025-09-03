"""
Configuration settings for the They Might Say application.
"""
import os
from typing import List, Optional
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation and type hints."""
    
    # Application
    app_name: str = "They Might Say"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # Database
    database_url: str
    redis_url: str = "redis://localhost:6379"
    
    # Authentication & Security
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # File Upload
    max_upload_size: str = "100MB"
    upload_dir: str = "/app/uploads"
    
    # AI/ML Configuration
    openai_api_key: Optional[str] = None
    embeddings_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4"
    
    # Vector Database
    vector_dimension: int = 1536
    chunk_size: int = 1000
    chunk_overlap: int = 100
    
    # Object Storage (MinIO)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket: str = "tms-sources"
    minio_secure: bool = False
    
    @validator('cors_origins', pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator('max_upload_size')
    def parse_upload_size(cls, v):
        """Convert string like '100MB' to bytes."""
        if isinstance(v, str):
            v = v.upper()
            if v.endswith('MB'):
                return int(v[:-2]) * 1024 * 1024
            elif v.endswith('GB'):
                return int(v[:-2]) * 1024 * 1024 * 1024
            elif v.endswith('KB'):
                return int(v[:-2]) * 1024
        return int(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings