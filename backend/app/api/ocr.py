import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import get_current_user, get_db
from app.ocr.correction import save_correction
from app.ocr.pipeline import process_schedule_image
from app.ocr.schemas import CorrectionCreate, CorrectionOut, ExtractedSchedule

router = APIRouter()


@router.post("/ocr/schedule", response_model=ExtractedSchedule)
def ocr_schedule(
    image: UploadFile = File(..., description="근무표 이미지"),
    _: object = Depends(get_current_user),  # 인증 필수
):
    """근무표 이미지를 OCR로 읽어 구조화 결과(경고·캘린더 미리보기 포함)를 돌려준다.

    미리보기용이므로 처리 후 임시 이미지는 바로 삭제한다(서버에 보관하지 않음).
    """
    contents = image.file.read()
    ext = (image.filename or "upload").rsplit(".", 1)[-1].lower()
    if ext not in ("jpg", "jpeg", "png", "webp"):
        ext = "png"

    tmp_dir = Path(settings.upload_dir) / "ocr_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    img_path = tmp_dir / f"{uuid.uuid4()}.{ext}"
    img_path.write_bytes(contents)

    try:
        return process_schedule_image(img_path)
    finally:
        for path in (img_path, img_path.with_suffix(".pre.png")):
            if path.exists():
                path.unlink()


@router.post("/ocr/corrections", response_model=CorrectionOut, status_code=201)
def ocr_correction(
    body: CorrectionCreate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),  # 인증 필수
):
    """사용자가 미리보기에서 고친 OCR 결과를 저장한다(학습용)."""
    return save_correction(db=db, data=body, store_image=settings.ocr_store_image)
