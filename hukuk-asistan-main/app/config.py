from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    
    # Google Gemini AI ayarları
    GEMINI_API_KEY: str
    
    # Yargıtay Scraper API ayarları
    SCRAPER_API_URL: str = "http://localhost:8001"
    
    # Genel ayarlar
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API ayarları
    API_TITLE: str = "Yargısal Zeka API"
    API_VERSION: str = "2.1.0"
    API_DESCRIPTION: str = "Yapay Zeka Destekli Yargıtay Kararı Arama Platformu"
    
    # Security ayarları
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS ayarları
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour in seconds
    
    # Google Cloud Firestore ayarları
    GCP_PROJECT_ID: str = ""
    FIRESTORE_DATABASE_ID: str = "(default)"
    
    # Production ayarları
    SSL_KEYFILE: str = ""
    SSL_CERTFILE: str = ""
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def cors_origins(self) -> List[str]:
        if self.is_production:
            # Production'da tüm origin'lere izin ver (domain henüz alınmadığı için)
            return ["*"]
        return self.CORS_ORIGINS

settings = Settings()