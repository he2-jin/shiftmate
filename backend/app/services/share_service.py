"""공유 링크 생성·조회·삭제 서비스."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models.schedule_cell import ScheduleCell
from app.db.models.schedule_month import ScheduleMonth
from app.db.models.schedule_person import SchedulePerson
from app.db.models.share_token import ShareToken
from app.db.models.user import User
from app.schemas.schedule import CellOut, PersonOut
from app.schemas.share import SharedScheduleResponse
from app.services.review_service import _cell_to_out


def create_share(
    db: Session,
    user: User,
    year: int,
    month: int,
    expires_in_days: int,
) -> ShareToken:
    """해당 월 공유 링크 생성. 같은 월 기존 링크는 교체."""
    sm = db.query(ScheduleMonth).filter_by(year=year, month=month).first()
    if sm is None:
        raise HTTPException(status_code=404, detail="해당 월의 근무표를 찾을 수 없습니다.")

    db.query(ShareToken).filter_by(user_id=user.id, schedule_month_id=sm.id).delete()

    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
    token = ShareToken(
        token=str(uuid.uuid4()),
        user_id=user.id,
        schedule_month_id=sm.id,
        year=year,
        month=month,
        expires_at=expires_at,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def get_share(db: Session, token_str: str) -> SharedScheduleResponse:
    """공유 토큰으로 근무 조회. 만료됐거나 없으면 404/410."""
    token = db.query(ShareToken).filter_by(token=token_str).first()
    if token is None:
        raise HTTPException(status_code=404, detail="공유 링크를 찾을 수 없습니다.")

    if token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="만료된 공유 링크입니다.")

    sm = db.get(ScheduleMonth, token.schedule_month_id)
    if sm is None or sm.active_version_id is None:
        raise HTTPException(status_code=404, detail="확정된 근무표가 없습니다.")

    person = (
        db.query(SchedulePerson)
        .filter_by(schedule_version_id=sm.active_version_id, user_id=token.user_id)
        .first()
    )
    if person is None:
        raise HTTPException(status_code=404, detail="연결된 근무자를 찾을 수 없습니다.")

    cells = (
        db.query(ScheduleCell)
        .filter_by(schedule_version_id=sm.active_version_id, schedule_person_id=person.id)
        .order_by(ScheduleCell.date)
        .all()
    )
    return SharedScheduleResponse(
        person=PersonOut.model_validate(person),
        year=token.year,
        month=token.month,
        cells=[_cell_to_out(c) for c in cells],
        expires_at=token.expires_at,
    )


def delete_share(db: Session, user: User, token_str: str) -> None:
    """공유 링크 삭제. 본인 링크만 가능."""
    token = db.query(ShareToken).filter_by(token=token_str).first()
    if token is None:
        raise HTTPException(status_code=404, detail="공유 링크를 찾을 수 없습니다.")
    if token.user_id != user.id:
        raise HTTPException(status_code=403, detail="본인의 공유 링크만 삭제할 수 있습니다.")
    db.delete(token)
    db.commit()
