"""Application configuration"""
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    
    # Authentication settings
    require_auth: bool = True  # Set to False to disable authentication
    access_token_lifetime_min: int = 15
    refresh_token_lifetime_days: int = 7
    reuse_lifetime_min: int = 1
    jwt_issuer: str = "l-inspector-backend"
    jwt_audience: str = "l-inspector-app"
    
    # RSA keys - can be provided directly as env vars or via file paths
    private_key: Optional[str] = None  # Direct key content from env var
    public_key: Optional[str] = None   # Direct key content from env var
    private_key_path: str = "private.pem"  # Fallback to file path
    public_key_path: str = "public.pem"    # Fallback to file path
    
    class Config:
        env_file = ".env"


settings = Settings()