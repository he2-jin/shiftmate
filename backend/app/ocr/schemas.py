"""OCR 파이프라인이 주고받는 데이터 모양 (Pydantic)."""

import datetime as dt
from typing import Annotated

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """글자가 사진의 어디에 있는지 (위치 상자)."""

    x: int
    y: int
    width: int
    height: int


class OcrWord(BaseModel):
    """OCR이 읽어낸 글자 하나."""

    text: str
    confidence: float | None = None
    bbox: BoundingBox | None = None


class OcrResult(BaseModel):
    """사진 읽기 도구의 원본 결과."""

    raw_text: Annotated[str, Field(description="읽어낸 전체 원문")] = ""
    words: list[OcrWord] = Field(default_factory=list)
    confidence: Annotated[float | None, Field(description="전체 평균 확실한 정도")] = None
    warnings: list[str] = Field(default_factory=list)


class ExtractedDay(BaseModel):
    """한 사람의 하루 근무."""

    day: Annotated[int, Field(description="며칠 (1~31)")]
    code: Annotated[str | None, Field(description="근무 코드 (D/E/N/OFF/연차/휴무/빈칸)")] = None
    confidence: float | None = None


class PersonSummary(BaseModel):
    """근무표 오른쪽 합계 (인식되면 채움)."""

    off: int | None = None
    n: int | None = None
    annual_leave: int | None = None


class ExtractedPerson(BaseModel):
    """한 근무자와 그의 날짜별 근무."""

    name: Annotated[str, Field(description="근무자 이름")]
    role: Annotated[str | None, Field(description="직책 (NA/지원인력 등)")] = None
    days: list[ExtractedDay] = Field(default_factory=list)
    summary: PersonSummary | None = None


class CalendarEvent(BaseModel):
    """캘린더 등록 전 미리보기용 일정 (실제 등록은 하지 않음)."""

    title: Annotated[str, Field(description="일정 제목 (예: 나이트 근무)")]
    start: dt.datetime
    end: dt.datetime | None = None
    all_day: bool = False
    source: str = "ocr_schedule"


class ExtractedSchedule(BaseModel):
    """근무표 사진을 읽어 구조화한 최종 결과."""

    source_type: str = "shift_schedule"
    year: int | None = None
    month: int | None = None
    people: list[ExtractedPerson] = Field(default_factory=list)
    ocr: OcrResult | None = None
    warnings: list[str] = Field(default_factory=list)
    calendar_preview: list[CalendarEvent] = Field(default_factory=list)


class CorrectionCreate(BaseModel):
    """사용자가 미리보기에서 OCR 값을 고쳐 보낼 때의 요청."""

    image_id: Annotated[str | None, Field(description="이미지 식별자(저장 설정 켜진 경우)")] = None
    user_id: Annotated[str | None, Field(description="사용자 식별자(로그인 도입 전엔 비움)")] = None
    original_code: Annotated[str | None, Field(description="OCR이 예측했던 코드")] = None
    original_confidence: float | None = None
    corrected_code: Annotated[str, Field(description="사용자가 고친 코드")]
    target_date: dt.date | None = None
    bbox: BoundingBox | None = None


class CorrectionOut(BaseModel):
    id: int
    corrected_code: str
    created_at: dt.datetime

    model_config = {"from_attributes": True}
