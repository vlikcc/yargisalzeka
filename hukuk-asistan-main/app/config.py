from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import json

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    
    # Google Gemini AI ayarları
    GEMINI_API_KEY: str
    
    # MongoDB Atlas ayarları
    MONGODB_CONNECTION_STRING: Optional[str] = None
    MONGODB_DATABASE_NAME: str = "yargisalzeka"
    
    # Yargıtay Scraper API ayarları
    SCRAPER_API_URL: str = "http://localhost:8001"
    
    # Security
    API_SECRET_KEY: Optional[str] = None
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # CORS ayarları
    CORS_ORIGINS: str = '["*"]'  # JSON string olarak
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = '["*"]'
    CORS_ALLOW_HEADERS: str = '["*"]'
    
    # Rate limiting
    USER_RATE_LIMIT: str = "10/minute"
    GLOBAL_RATE_LIMIT: str = "1000/hour"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: Optional[str] = None
    LOG_MAX_SIZE: str = "100MB"
    LOG_BACKUP_COUNT: int = 10
    
    # Performance
    REQUEST_TIMEOUT: int = 30
    MAX_WORKERS: int = 4
    
    # API ayarları
    API_TITLE: str = "Yargısal Zeka API"
    API_VERSION: str = "2.1.0"
    API_DESCRIPTION: str = "Yapay Zeka Destekli Yargıtay Kararı Arama Platformu"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """CORS origins'i liste olarak döndür"""
        try:
            return json.loads(self.CORS_ORIGINS)
        except:
            return ["*"]
    
    @property
    def cors_methods_list(self) -> List[str]:
        """CORS methods'u liste olarak döndür"""
        try:
            return json.loads(self.CORS_ALLOW_METHODS)
        except:
            return ["*"]
    
    @property
    def cors_headers_list(self) -> List[str]:
        """CORS headers'ı liste olarak döndür"""
        try:
            return json.loads(self.CORS_ALLOW_HEADERS)
        except:
            return ["*"]
    
    @property
    def is_production(self) -> bool:
        """Production ortamında mıyız?"""
        return self.ENVIRONMENT.lower() == "production"

settings = Settings()