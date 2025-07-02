"""
Configuration module for the Travel Planner API.
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class."""
    
    # API Keys
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    GOOGLE_PLACES_API_KEY: Optional[str] = os.getenv("GOOGLE_PLACES_API_KEY", GOOGLE_API_KEY)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # FastAPI Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    
    # App Settings
    APP_NAME: str = "Travel Planner API"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "API for generating travel plans based on user preferences using LangChain."
    
    # Scraping Settings
    REQUEST_TIMEOUT: int = 15
    MAX_RETRIES: int = 3
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    def validate_api_keys(self):
        """Validate required API keys are present"""
        warnings = []
        
        if not self.GOOGLE_API_KEY:
            warnings.append("GOOGLE_API_KEY not set")
        if not self.GOOGLE_PLACES_API_KEY:
            warnings.append("GOOGLE_PLACES_API_KEY not set (using mock data)")
            
        return {
            "has_required_keys": bool(self.GOOGLE_API_KEY),
            "warnings": warnings
        }

config = Config()