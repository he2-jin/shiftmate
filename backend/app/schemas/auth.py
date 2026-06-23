"""Auth API 요청·응답 Pydantic 스키마."""

import datetime as dt

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """회원가입 요청 — 이메일과 비밀번호 (8자 이상)."""

    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    """로그인 요청."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """로그인 성공 응답 — access·refresh 토큰 한 쌍."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    """토큰 갱신 응답 — 새 access 토큰만 반환."""

    access_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """토큰 갱신 요청 — refresh_token 전달."""

    refresh_token: str


class UserOut(BaseModel):
    """회원가입 완료 응답 — 생성된 사용자 정보."""

    id: int
    email: str
    created_at: dt.datetime

    model_config = {"from_attributes": True}
