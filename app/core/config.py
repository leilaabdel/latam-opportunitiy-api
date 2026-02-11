# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Salesforce OAuth settings
    SALESFORCE_CLIENT_ID: str
    SALESFORCE_CLIENT_SECRET: str
    SALESFORCE_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    SALESFORCE_DOMAIN: str = "login.salesforce.com"  # or test.salesforce.com for sandbox
    
    # Encryption key for storing refresh tokens
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    ENCRYPTION_KEY: str
    
    # MongoDB settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "fortinet_sf"
    
    # API settings (optional - for your own API auth if needed)
    API_SECRET_KEY: Optional[str] = None
    API_ALGORITHM: str = "HS256"
    API_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Environment
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()