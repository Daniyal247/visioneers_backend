from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/visioneers_marketplace"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # AI Providers
    openai_api_key: Optional[str] = "42357e03af9a47afb7293108c9c1534f"
    openai_api_base: Optional[str] = "https://kaispeazureai.openai.azure.com/"
    openai_api_version: str = "2024-02-15-preview"
    openai_deployment_name: Optional[str] = "gpt-4o"
    anthropic_api_key: Optional[str] = None
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Application
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000", "http://127.0.0.1:8080"]
    
    # File Upload
    max_file_size: int = 10485760  # 10MB
    upload_dir: str = "uploads/"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # Production Settings
    postgres_user: str = "visioneers_user"
    postgres_password: str = "visioneers_password"
    
    # AI Agent
    agent_model: str = "gpt-4o"
    agent_temperature: float = 0.7
    max_conversation_history: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields from environment


settings = Settings() 