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
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Application
    debug: bool = True
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # File Upload
    max_file_size: int = 10485760  # 10MB
    upload_dir: str = "uploads/"
    
    # AI Agent
    agent_model: str = "gpt-4"
    agent_temperature: float = 0.7
    max_conversation_history: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 