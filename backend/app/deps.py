"""FastAPI 공통 의존성 — DB 세션, 현재 로그인 사용자."""

from collections.abc import Generator

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import SessionLocal

_security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    """요청마다 DB 세션 생성 후 종료 시 반환."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
    db: Session = Depends(get_db),
):
    """Bearer 토큰 검증 후 User 반환. 실패 시 401."""
    from app.db.models.user import User
    from app.services.auth_service import decode_token

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
    return user
