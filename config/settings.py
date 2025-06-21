import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

class Settings(BaseSettings):
    # Application Settings
    app_name: str = "Empirion Genesis System"
    version: str = "1.0.0"
    debug: bool = True
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    websocket_port: int = 8765
    
    # Database Settings
    database_url: str = "sqlite:///./data/empirion.db"
    database_echo: bool = False
    
    # Security
    secret_key: str = "empirion-genesis-secret-key-2025"
    access_token_expire_minutes: int = 30
    
    # Agent Settings
    max_agents: int = 100
    agent_evolution_interval: float = 1.0
    quantum_processing_enabled: bool = True
    
    # Optimization Settings
    optimization_level: float = 1.0
    infinite_optimization: bool = False
    memory_limit_mb: int = 1024
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/empirion.log"
    
    # WebSocket Settings
    websocket_heartbeat: int = 30
    max_connections: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
