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

    upload_dir: str = "/data/uploads"
    max_upload_mb: int = 10
    parser_backend: str = "mock"

    # OCR (Phase 8) — 기본은 셀 분할(로컬, 외부 전송 없음)
    ocr_engine: str = "cell_split"
    ocr_store_image: bool = False  # 수정 기록에 원본 이미지 식별자를 남길지


settings = Settings()
