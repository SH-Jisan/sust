import os
from dotenv import load_dotenv

# Load local environment variables from .env if present
load_dotenv()

class Settings:
    PORT: int = int(os.getenv("PORT", "8000"))
    ENV: str = os.getenv("ENV", "development")
    
    # LLM configurations
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-1.5-flash")
    
    # Secrets
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

settings = Settings()
