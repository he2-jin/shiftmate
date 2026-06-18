import datetime as dt

from sqlalchemy import Date, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OcrCorrection(Base):
    """사용자가 미리보기에서 OCR 결과를 고친 기록 (나중에 학습용).

    개인정보 보호: 원본 이미지 저장 여부는 설정(ocr_store_image)으로 분리한다.
    이미지를 저장하지 않아도 (원래 예측·고친 값·위치)만으로 기록을 남길 수 있다.
    """

    __tablename__ = "ocr_correction"

    id: Mapped[int] = mapped_column(primary_key=True)
    image_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    original_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    original_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    corrected_code: Mapped[str] = mapped_column(String(32), nullable=False)
    target_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)

    bbox_x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_y: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
