import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://devmustafatavasli:@localhost:5432/boranalytics"
    )
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # CORS Origins (comma separated)
    ALLOWED_ORIGINS: str = os.getenv(
        "ALLOWED_ORIGINS", 
        "http://localhost:5173,http://localhost:3000"
    )
    
    @property
    def cors_origins(self):
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

settings = Settings()
