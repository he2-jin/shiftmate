"""비밀번호 해싱과 JWT 생성·검증 — 인증 서비스 핵심 로직."""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings


def hash_password(password: str) -> str:
    """평문 비밀번호 → bcrypt 해시 반환."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """평문과 해시가 일치하면 True."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: int, email: str) -> str:
    """user_id·email을 담은 단기(1시간) JWT 반환."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_refresh_token(user_id: int) -> str:
    """user_id를 담은 장기(30일) JWT 반환."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict | None:
    """JWT 검증 후 payload 반환. 만료·위조 시 None."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError:
        return None
