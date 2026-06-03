import datetime as dt
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models.schedule_cell import (
    SHIFT_D, SHIFT_E, SHIFT_LEAVE, SHIFT_N, SHIFT_OFF, ScheduleCell,
)
from app.db.models.schedule_version import STATUS_DRAFT, ScheduleVersion
from app.schemas.schedule import (
    CONFIDENCE_REVIEW_THRESHOLD,
    CellOut,
    CellPatchResponse,
    PersonOut,
    ReviewResponse,
    ScheduleMonthOut,
    VersionDetailResponse,
)

VALID_SHIFT_CODES = {SHIFT_D, SHIFT_E, SHIFT_N, SHIFT_OFF, SHIFT_LEAVE}


def _cell_to_out(cell: ScheduleCell) -> CellOut:
    score = cell.confidence_score
    return CellOut(
        cell_id=cell.id,
        person_id=cell.schedule_person_id,
        date=cell.date,
        shift_code=cell.corrected_value if cell.is_user_corrected else cell.shift_code,
        confidence_score=score,
        is_user_corrected=cell.is_user_corrected,
        needs_review=score is not None and score < CONFIDENCE_REVIEW_THRESHOLD,
    )


def get_version_detail(db: Session, version_id: int) -> VersionDetailResponse:
    version = db.query(ScheduleVersion).filter_by(id=version_id).first()
    if version is None:
        raise HTTPException(status_code=404, detail="버전을 찾을 수 없습니다.")

    from app.db.models.schedule_month import ScheduleMonth
    from app.db.models.schedule_person import SchedulePerson

    month = db.query(ScheduleMonth).filter_by(id=version.schedule_month_id).first()
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

    # table_type은 persons에서 가져옴 (모두 같은 값)
    table_type = persons[0].table_type if persons else ""

    return VersionDetailResponse(
        version_id=version.id,
        status=version.status,
        schedule_month=ScheduleMonthOut.model_validate(month),
        table_type=table_type,
        created_at=version.created_at,
        updated_at=version.updated_at,
        persons=[PersonOut.model_validate(p) for p in persons],
        cells=[_cell_to_out(c) for c in cells],
    )


def patch_cell(db: Session, cell_id: int, shift_code: str) -> CellPatchResponse:
    shift_code = shift_code.upper()
    if shift_code not in VALID_SHIFT_CODES:
        raise HTTPException(
            status_code=422,
            detail=f"유효하지 않은 근무 코드입니다. 허용: {', '.join(sorted(VALID_SHIFT_CODES))}",
        )

    cell = db.query(ScheduleCell).filter_by(id=cell_id).first()
    if cell is None:
        raise HTTPException(status_code=404, detail="셀을 찾을 수 없습니다.")

    cell.corrected_value = shift_code
    cell.is_user_corrected = True
    db.commit()
    db.refresh(cell)

    score = cell.confidence_score
    return CellPatchResponse(
        cell_id=cell.id,
        person_id=cell.schedule_person_id,
        date=cell.date,
        shift_code=shift_code,
        confidence_score=score,
        is_user_corrected=True,
        needs_review=score is not None and score < CONFIDENCE_REVIEW_THRESHOLD,
    )


def complete_review(db: Session, version_id: int) -> ReviewResponse:
    version = db.query(ScheduleVersion).filter_by(id=version_id).first()
    if version is None:
        raise HTTPException(status_code=404, detail="버전을 찾을 수 없습니다.")
    if version.status != STATUS_DRAFT:
        raise HTTPException(
            status_code=409, detail="초안(draft) 상태인 버전만 검토 완료 처리할 수 있습니다."
        )

    # 이미지 파일 삭제
    image_deleted = False
    if version.source_image_path:
        image_path = Path(version.source_image_path)
        if image_path.exists():
            image_path.unlink()
            image_deleted = True
        version.source_image_path = None

    now = dt.datetime.now(dt.timezone.utc)
    version.status = "reviewed"
    version.reviewed_at = now
    db.commit()
    db.refresh(version)

    return ReviewResponse(
        version_id=version.id,
        status=version.status,
        reviewed_at=version.reviewed_at,
        image_deleted=image_deleted,
    )
