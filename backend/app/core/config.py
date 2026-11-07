from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "TalentHub"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "talenthub-super-secret-key-change-in-production-2026-min-32-chars-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # Paths
    ROOT_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')), 'talenthub.db').replace(chr(92), '/')}"
    SYNC_DATABASE_URL: str = f"sqlite:///{os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')), 'talenthub.db').replace(chr(92), '/')}"
    
    # File Storage
    STORAGE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage"))
    OFFERS_STORAGE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage/offers"))
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )

settings = Settings()

# Ensure storage directories exist
os.makedirs(settings.OFFERS_STORAGE_DIR, exist_ok=True)
