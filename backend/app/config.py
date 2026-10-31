from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_name: str = "sivamani_db"
    db_user: str = "sivamani_user"
    db_password: str = "Dsm_5885"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()