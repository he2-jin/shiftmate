"""사용자가 고친 OCR 결과를 저장하는 서비스 (학습 데이터)."""

from sqlalchemy.orm import Session

from app.db.models.ocr_correction import OcrCorrection
from app.ocr.schemas import CorrectionCreate


def save_correction(
    db: Session, data: CorrectionCreate, store_image: bool = False
) -> OcrCorrection:
    """수정 기록을 저장한다.

    개인정보 보호: store_image=False면 이미지 식별자를 남기지 않는다
    (원본 이미지 없이 예측·수정·위치만 학습용으로 보관).
    """
    bbox = data.bbox
    row = OcrCorrection(
        image_id=data.image_id if store_image else None,
        user_id=data.user_id,
        original_code=data.original_code,
        original_confidence=data.original_confidence,
        corrected_code=data.corrected_code,
        target_date=data.target_date,
        bbox_x=bbox.x if bbox else None,
        bbox_y=bbox.y if bbox else None,
        bbox_width=bbox.width if bbox else None,
        bbox_height=bbox.height if bbox else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
