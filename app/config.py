"""Application configuration"""
from typing import Optional
from pydantic_settings import BaseSettings
from urllib.parse import urlparse, urlunparse


class Settings(BaseSettings):
    database_url: str
    database_password: Optional[str] = None  # Optional override for database password
    db_driver: str = "asyncpg"  # Options: "asyncpg" or "psycopg2"
    
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
    
    # Logging settings
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_json: bool = True  # Enable structured JSON logging
    
    class Config:
        env_file = ".env"
    
    def get_database_url(self) -> str:
        """Get database URL with password override if provided"""
        if self.database_password is None:
            return self.database_url
        
        # Parse the URL and replace the password
        parsed = urlparse(self.database_url)
        
        # Reconstruct netloc with new password
        if parsed.username:
            netloc = f"{parsed.username}:{self.database_password}@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
        else:
            netloc = parsed.netloc
        
        # Reconstruct the full URL
        return urlunparse((
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))


settings = Settings()