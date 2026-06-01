from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "shiftmate"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://shiftmate:shiftmate@db:5432/shiftmate"


settings = Settings()
