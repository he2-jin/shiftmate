"""사용자 관련 Pydantic 스키마."""

import datetime as dt

from pydantic import BaseModel, ConfigDict


class UserMeOut(BaseModel):
    """내 정보 응답 — 계정 기본 정보."""

    id: int
    email: str
    is_active: bool
    created_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class PersonLinkRequest(BaseModel):
    """근무자 연결 요청 — 내 이름에 해당하는 person_id 선택."""

    person_id: int
