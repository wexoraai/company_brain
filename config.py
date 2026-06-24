import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load env file if it exists
load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite+aiosqlite:///company_brain.db"
    )
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super_secret_signing_key")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Mock key settings
    ZOHO_CRM_API_KEY: str = os.getenv("ZOHO_CRM_API_KEY", "mock_zoho_crm_key")
    ZOHO_BOOKS_API_KEY: str = os.getenv("ZOHO_BOOKS_API_KEY", "mock_zoho_books_key")
    RETELL_API_KEY: str = os.getenv("RETELL_API_KEY", "mock_retell_key")

    # Supabase configurations
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_BUCKET: str = os.getenv("SUPABASE_BUCKET", "company-brain-docs")

    class Config:
        case_sensitive = True

settings = Settings()
