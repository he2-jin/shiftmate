"""OCR 처리 단계들을 순서대로 이어 실행하는 묶음.

사진 다듬기 → 글자 읽기 → 표로 맞추기 → 경고 달기 → 캘린더 미리보기.
"""

from pathlib import Path

from app.ocr.calendar import convert_shift_to_calendar_events
from app.ocr.engine import OcrEngine, TesseractOcrEngine
from app.ocr.parse import parse_schedule
from app.ocr.preprocess import ImagePreprocessor
from app.ocr.schemas import ExtractedSchedule
from app.ocr.validate import validate_schedule_extraction


def _build_engine() -> OcrEngine:
    """설정(ocr_engine)에 따라 OCR 엔진을 고른다.

    기본을 셀 분할(cell_split)로 둔 이유:
    - 표를 셀 단위로 잘라 읽어 통짜 OCR보다 정확도가 높음
    - 완전 로컬 처리 → 근무표 속 동료(제3자) 정보를 외부로 보내지 않음
    """
    from app.config import settings

    if settings.ocr_engine == "cell_split":
        from app.ocr.cell_split import CellSplitOcrEngine

        return CellSplitOcrEngine()
    return TesseractOcrEngine()


def process_schedule_image(
    image_path: Path,
    engine: OcrEngine | None = None,
    preprocessor: ImagePreprocessor | None = None,
    shift_time_settings: dict[str, dict] | None = None,
) -> ExtractedSchedule:
    """근무표 이미지를 받아 구조화된 결과(경고·캘린더 미리보기 포함)를 돌려준다."""
    engine = engine or _build_engine()
    preprocessor = preprocessor or ImagePreprocessor()

    # 1. 사진 다듬기 (실패해도 원본으로 진행)
    try:
        ocr_input = preprocessor.preprocess(image_path)
    except Exception:  # noqa: BLE001
        ocr_input = image_path

    # 2. 글자 읽기
    ocr = engine.recognize(ocr_input)

    # 3. 표로 맞추기
    schedule = parse_schedule(ocr)

    # 4. 경고 모으기 (OCR 단계 경고 + 구조 검증 경고)
    schedule.warnings = list(ocr.warnings) + validate_schedule_extraction(schedule)

    # 5. 캘린더 미리보기
    schedule.calendar_preview = convert_shift_to_calendar_events(
        schedule, shift_time_settings
    )

    return schedule
