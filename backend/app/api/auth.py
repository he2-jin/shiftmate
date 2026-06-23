"""회원가입·로그인·토큰 갱신·로그아웃 엔드포인트."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.deps import get_db
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
_security = HTTPBearer()


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """이메일+비밀번호로 계정 생성. 중복 이메일은 400 반환."""
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")
    user = User(email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """이메일+비밀번호 검증 후 access·refresh 토큰 반환."""
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)

    user.refresh_token = refresh_token
    db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """refresh_token 검증 후 새 access_token 반환."""
    payload = decode_token(body.refresh_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="유효하지 않은 refresh token입니다.")

    user = db.get(User, int(payload["sub"]))
    if user is None or user.refresh_token != body.refresh_token:
        raise HTTPException(status_code=401, detail="만료되었거나 이미 로그아웃된 토큰입니다.")

    return AccessTokenResponse(access_token=create_access_token(user.id, user.email))


@router.post("/logout", status_code=204)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
    db: Session = Depends(get_db),
):
    """access_token 검증 후 DB의 refresh_token 무효화."""
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    user = db.get(User, int(payload["sub"]))
    if user:
        user.refresh_token = None
        db.commit()
