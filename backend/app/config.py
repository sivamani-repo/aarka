import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AARKA"
    app_tagline: str = "Solar Operations, Simplified."
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_name: str = "aarka_db"
    db_user: str = "sivamani_user"
    db_password: str = "Dsm_5885"

    secret_key: str = "aarka-secret-jwt-key-for-development-2026"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    upload_dir: str = "uploads"

    # Frontend & Backend Origin
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://127.0.0.1:8000"

    # Google OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    # SMTP / Email Configuration
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_tls: bool = True
    emails_from_email: str = "noreply@aarka.com"
    emails_from_name: str = "AARKA Solar Operations"

    # Token Lifespans
    verification_token_expire_hours: int = 24
    reset_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
