from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models.schedule_cell import ScheduleCell
from app.db.models.schedule_month import ScheduleMonth
from app.db.models.schedule_person import SchedulePerson
from app.schemas.schedule import (
    MonthScheduleResponse,
    PersonOut,
    PersonScheduleResponse,
    ScheduleMonthOut,
)
from app.services.review_service import _cell_to_out


def _get_month(db: Session, year: int, month: int) -> ScheduleMonth:
    m = db.query(ScheduleMonth).filter_by(year=year, month=month).first()
    if m is None:
        raise HTTPException(status_code=404, detail="해당 월의 근무표를 찾을 수 없습니다.")
    return m


def get_month_schedule(db: Session, year: int, month: int) -> MonthScheduleResponse:
    """그 달의 확정본(active_version) 근무표를 반환한다. 확정본이 없으면 404."""
    m = _get_month(db, year, month)
    if m.active_version_id is None:
        raise HTTPException(status_code=404, detail="확정된 근무표가 없습니다.")

    version_id = m.active_version_id
    persons = (
        db.query(SchedulePerson)
        .filter_by(schedule_version_id=version_id)
        .order_by(SchedulePerson.row_index)
        .all()
    )
    cells = (
        db.query(ScheduleCell)
        .filter_by(schedule_version_id=version_id)
        .order_by(ScheduleCell.schedule_person_id, ScheduleCell.date)
        .all()
    )
    table_type = persons[0].table_type if persons else ""

    return MonthScheduleResponse(
        schedule_month=ScheduleMonthOut.model_validate(m),
        active_version_id=version_id,
        table_type=table_type,
        persons=[PersonOut.model_validate(p) for p in persons],
        cells=[_cell_to_out(c) for c in cells],
    )


def get_person_schedule(
    db: Session, year: int, month: int, person_id: int
) -> PersonScheduleResponse:
    """확정본 안에서 한 근무자의 근무 셀만 반환한다."""
    m = _get_month(db, year, month)
    if m.active_version_id is None:
        raise HTTPException(status_code=404, detail="확정된 근무표가 없습니다.")

    person = (
        db.query(SchedulePerson)
        .filter_by(id=person_id, schedule_version_id=m.active_version_id)
        .first()
    )
    if person is None:
        raise HTTPException(status_code=404, detail="해당 근무자를 찾을 수 없습니다.")

    cells = (
        db.query(ScheduleCell)
        .filter_by(schedule_version_id=m.active_version_id, schedule_person_id=person_id)
        .order_by(ScheduleCell.date)
        .all()
    )
    return PersonScheduleResponse(
        person=PersonOut.model_validate(person),
        year=year,
        month=month,
        cells=[_cell_to_out(c) for c in cells],
    )
