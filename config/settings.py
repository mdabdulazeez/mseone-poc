"""
Configuration settings for DevOps PoC
Manages Azure service connections and API settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Azure Configuration (PoC Requirements)
    AZURE_TENANT_ID: str
    AZURE_CLIENT_ID: str
    AZURE_CLIENT_SECRET: str
    AZURE_SUBSCRIPTION_ID: str
    
    # Azure AD Authentication (PoC Requirement)
    AZURE_AD_AUTHORITY: str
    AZURE_AD_AUDIENCE: str
    
    # CosmosDB Configuration (PoC Requirement)
    COSMOS_DB_URI: str
    COSMOS_DB_KEY: str
    COSMOS_DB_DATABASE: str = "devops-poc"
    COSMOS_DB_CONTAINER: str = "projects"
    
    # Azure Storage Configuration (PoC Requirement)
    STORAGE_ACCOUNT_NAME: str
    STORAGE_CONNECTION_STRING: str
    STORAGE_CONTAINER_NAME: str = "api-results"
    
    # Logic Apps Configuration (PoC Requirement)
    LOGIC_APP_TRIGGER_URL: str = ""
    TEAMS_WEBHOOK_URL: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Validate required Azure settings
def validate_azure_config():
    """Validate that all required Azure configurations are present"""
    settings = get_settings()
    required_fields = [
        "AZURE_TENANT_ID",
        "AZURE_CLIENT_ID", 
        "COSMOS_DB_URI",
        "STORAGE_ACCOUNT_NAME"
    ]
    
    missing_fields = []
    for field in required_fields:
        if not getattr(settings, field, None):
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required Azure configuration: {missing_fields}")
    
    return True


