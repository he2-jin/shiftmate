import datetime as dt

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models.schedule_month import ScheduleMonth
from app.db.models.schedule_version import (
    STATUS_APPLIED,
    STATUS_DRAFT,
    STATUS_IGNORED,
    STATUS_REVIEWED,
    ScheduleVersion,
)
from app.schemas.schedule import ApplyResponse, IgnoreResponse


def apply_version(db: Session, version_id: int) -> ApplyResponse:
    """검토 완료(reviewed) 버전을 그 달의 확정본(applied)으로 지정한다.

    같은 달에 기존 확정본이 있으면 reviewed로 되돌리고, active 표시를 새 버전으로 옮긴다.
    (한 달에 확정본은 항상 하나)
    """
    version = db.query(ScheduleVersion).filter_by(id=version_id).first()
    if version is None:
        raise HTTPException(status_code=404, detail="버전을 찾을 수 없습니다.")
    if version.status != STATUS_REVIEWED:
        raise HTTPException(
            status_code=409,
            detail="검토 완료(reviewed) 상태인 버전만 확정할 수 있습니다.",
        )

    month = db.query(ScheduleMonth).filter_by(id=version.schedule_month_id).first()
    previous_active_version_id = month.active_version_id

    # 기존 확정본을 reviewed로 되돌림 (자기 자신이 아닌 경우)
    if (
        previous_active_version_id is not None
        and previous_active_version_id != version_id
    ):
        prev = (
            db.query(ScheduleVersion)
            .filter_by(id=previous_active_version_id)
            .first()
        )
        if prev is not None:
            prev.status = STATUS_REVIEWED
            prev.applied_at = None

    version.status = STATUS_APPLIED
    version.applied_at = dt.datetime.now(dt.timezone.utc)
    month.active_version_id = version.id
    db.commit()
    db.refresh(version)
    db.refresh(month)

    return ApplyResponse(
        version_id=version.id,
        status=version.status,
        applied_at=version.applied_at,
        active_version_id=month.active_version_id,
        previous_active_version_id=previous_active_version_id,
    )


def ignore_version(db: Session, version_id: int) -> IgnoreResponse:
    """초안(draft) 또는 검토 완료(reviewed) 버전을 버림(ignored) 처리한다."""
    version = db.query(ScheduleVersion).filter_by(id=version_id).first()
    if version is None:
        raise HTTPException(status_code=404, detail="버전을 찾을 수 없습니다.")
    if version.status not in (STATUS_DRAFT, STATUS_REVIEWED):
        raise HTTPException(
            status_code=409,
            detail="초안(draft) 또는 검토 완료(reviewed) 상태인 버전만 버릴 수 있습니다.",
        )

    version.status = STATUS_IGNORED
    db.commit()
    db.refresh(version)

    return IgnoreResponse(version_id=version.id, status=version.status)
