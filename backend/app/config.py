import os
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

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
