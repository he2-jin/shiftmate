"""공유 링크 생성·조회·삭제 API."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.deps import get_current_user, get_db
from app.schemas.share import ShareCreateRequest, SharedScheduleResponse, ShareOut
from app.services.share_service import create_share, delete_share, get_share

router = APIRouter(prefix="/shares", tags=["shares"])


@router.post("", response_model=ShareOut, status_code=201)
def create_share_link(
    body: ShareCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """내 근무 공유 링크 생성. 같은 월 기존 링크는 교체."""
    return create_share(
        db=db,
        user=current_user,
        year=body.year,
        month=body.month,
        expires_in_days=body.expires_in_days,
    )


@router.get("/{token}", response_model=SharedScheduleResponse)
def view_shared_schedule(
    token: str,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),  # 로그인 필수
):
    """공유 링크로 근무 조회. 만료 시 410."""
    return get_share(db=db, token_str=token)


@router.delete("/{token}", status_code=204)
def delete_share_link(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """공유 링크 삭제. 본인만 가능."""
    delete_share(db=db, user=current_user, token_str=token)
