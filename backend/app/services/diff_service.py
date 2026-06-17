import datetime as dt

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models.schedule_cell import ScheduleCell
from app.db.models.schedule_month import ScheduleMonth
from app.db.models.schedule_person import SchedulePerson
from app.db.models.schedule_version import ScheduleVersion
from app.schemas.schedule import DiffCell, DiffResponse


def _shift_by_name_date(db: Session, version_id: int) -> dict[tuple[str, dt.date], str]:
    """(근무자 이름, 날짜) → 근무 코드. 고친 칸은 고친 값을 사용."""
    names = {
        p.id: p.name
        for p in db.query(SchedulePerson).filter_by(schedule_version_id=version_id)
    }
    result: dict[tuple[str, dt.date], str] = {}
    cells = db.query(ScheduleCell).filter_by(schedule_version_id=version_id).all()
    for c in cells:
        name = names.get(c.schedule_person_id)
        if name is None:
            continue
        code = c.corrected_value if c.is_user_corrected else c.shift_code
        result[(name, c.date)] = code
    return result


def diff_against_active(db: Session, version_id: int) -> DiffResponse:
    """대상 버전을 그 달의 확정본(active_version)과 이름·날짜 기준으로 비교한다."""
    version = db.query(ScheduleVersion).filter_by(id=version_id).first()
    if version is None:
        raise HTTPException(status_code=404, detail="버전을 찾을 수 없습니다.")

    month = db.query(ScheduleMonth).filter_by(id=version.schedule_month_id).first()
    active_id = month.active_version_id if month else None

    # 비교할 확정본이 없거나, 대상이 곧 확정본이면 비교 결과 없음
    if active_id is None or active_id == version_id:
        return DiffResponse(
            version_id=version_id, compared_to_version_id=None, changes=[]
        )

    target = _shift_by_name_date(db, version_id)
    base = _shift_by_name_date(db, active_id)

    changes = [
        DiffCell(
            person_name=name,
            date=date,
            from_shift=base[(name, date)],
            to_shift=to_code,
        )
        for (name, date), to_code in target.items()
        if (name, date) in base and base[(name, date)] != to_code
    ]
    changes.sort(key=lambda c: (c.person_name, c.date))

    return DiffResponse(
        version_id=version_id,
        compared_to_version_id=active_id,
        changes=changes,
    )
