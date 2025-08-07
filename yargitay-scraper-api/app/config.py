from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import json

class Settings(BaseSettings):
    # .env dosyasından ayarları okumak için yapılandırma
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # MongoDB Atlas ayarları
    MONGODB_CONNECTION_STRING: Optional[str] = None
    MONGODB_DATABASE_NAME: str = "yargisalzeka"
    
    # Scraper ayarları
    LOG_LEVEL: str = "INFO"
    USER_RATE_LIMIT: str = "10/minute"
    GLOBAL_RATE_LIMIT: str = "1000/hour"
    MAX_PAGES_TO_SEARCH: int = 5
    TARGET_RESULTS_PER_KEYWORD: int = 3
    SELENIUM_GRID_URL: str = "http://selenium-hub:4444/wd/hub"
    
    # Security
    API_SECRET_KEY: Optional[str] = None
    
    # CORS ayarları
    CORS_ORIGINS: str = '["*"]'  # JSON string olarak
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = '["*"]'
    CORS_ALLOW_HEADERS: str = '["*"]'
    
    # Logging
    LOG_FILE_PATH: Optional[str] = None
    LOG_MAX_SIZE: str = "100MB"
    LOG_BACKUP_COUNT: int = 10
    
    # Performance
    REQUEST_TIMEOUT: int = 30
    MAX_WORKERS: int = 4
    
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

# Ayarları import edilebilir bir nesne olarak oluştur
settings = Settings()