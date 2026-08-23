"""config/settings.py: Application configuration and environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Supabase / PostgreSQL Connection
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

    # AI API Keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    CEREBRAS_API_KEY: str = os.getenv("CEREBRAS_API_KEY", "")
    CLOUDFLARE_ACCOUNT_ID: str = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
    CLOUDFLARE_API_TOKEN: str = os.getenv("CLOUDFLARE_API_TOKEN", "")


settings = Settings()
