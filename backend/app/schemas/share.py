"""공유 링크 관련 Pydantic 스키마."""

import datetime as dt
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.schedule import CellOut, PersonOut


class ShareCreateRequest(BaseModel):
    """공유 링크 생성 요청 — 대상 월과 유효기간(일) 선택."""

    year: int
    month: int = Field(ge=1, le=12)
    expires_in_days: int = Field(ge=1, le=365)


class ShareOut(BaseModel):
    """공유 링크 생성 응답 — 토큰 및 만료 정보."""

    token: Annotated[str, Field(description="공유 토큰 (UUID)")]
    year: int
    month: int
    expires_at: Annotated[dt.datetime, Field(description="링크 만료 시각")]

    model_config = ConfigDict(from_attributes=True)


class SharedScheduleResponse(BaseModel):
    """공유 링크로 조회한 근무 정보 응답."""

    person: Annotated[PersonOut, Field(description="공유한 근무자 정보")]
    year: int
    month: int
    cells: Annotated[list[CellOut], Field(description="해당 근무자의 근무 셀 목록")]
    expires_at: Annotated[dt.datetime, Field(description="이 공유 링크의 만료 시각")]
