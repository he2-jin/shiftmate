"""사용자 정보 및 근무자 연결 API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models.schedule_cell import ScheduleCell
from app.db.models.schedule_month import ScheduleMonth
from app.db.models.schedule_person import SchedulePerson
from app.db.models.user import User
from app.deps import get_current_user, get_db
from app.schemas.schedule import PersonOut, PersonScheduleResponse
from app.schemas.user import PersonLinkRequest, UserMeOut
from app.services.review_service import _cell_to_out
from app.services.user_service import link_user_to_person

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMeOut)
def get_me(current_user: User = Depends(get_current_user)):
    """현재 로그인 사용자 정보 반환."""
    return current_user


@router.patch("/me/person", response_model=UserMeOut)
def patch_me_person(
    body: PersonLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """근무표에서 내 이름 선택 — 계정과 근무자 연결."""
    link_user_to_person(db=db, user=current_user, person_id=body.person_id)
    db.refresh(current_user)
    return current_user


@router.get("/me/schedules/{year}/{month}", response_model=PersonScheduleResponse)
def get_my_schedule(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """로그인한 사용자의 해당 월 근무 조회. 근무자 미연결 시 404."""
    sm = db.query(ScheduleMonth).filter_by(year=year, month=month).first()
    if sm is None or sm.active_version_id is None:
        raise HTTPException(status_code=404, detail="확정된 근무표가 없습니다.")

    person = (
        db.query(SchedulePerson)
        .filter_by(schedule_version_id=sm.active_version_id, user_id=current_user.id)
        .first()
    )
    if person is None:
        raise HTTPException(
            status_code=404, detail="연결된 근무자가 없습니다. 내 이름을 먼저 선택해 주세요."
        )

    cells = (
        db.query(ScheduleCell)
        .filter_by(schedule_version_id=sm.active_version_id, schedule_person_id=person.id)
        .order_by(ScheduleCell.date)
        .all()
    )
    return PersonScheduleResponse(
        person=PersonOut.model_validate(person),
        year=year,
        month=month,
        cells=[_cell_to_out(c) for c in cells],
    )
