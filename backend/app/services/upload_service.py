import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models.schedule_cell import ScheduleCell
from app.db.models.schedule_month import ScheduleMonth
from app.db.models.schedule_person import SchedulePerson
from app.db.models.schedule_version import (
    STATUS_DRAFT,
    STATUS_REVIEWED,
    ScheduleVersion,
)
from app.parsers.base import ScheduleParser
from app.schemas.schedule import (
    CONFIDENCE_REVIEW_THRESHOLD,
    CellOut,
    PersonOut,
    ScheduleMonthOut,
    UploadResponse,
)


def upload_and_parse(
    db: Session,
    file: UploadFile,
    year: int,
    month: int,
    table_type: str,
    settings: Settings,
    parser: ScheduleParser,
) -> UploadResponse:
    # 1. 파일 크기 검증
    contents = file.file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=413, detail=f"파일 크기가 {settings.max_upload_mb}MB를 초과했습니다.")

    # 2. 이미지 형식 검증 (JPEG/PNG/WEBP)
    import io
    try:
        img = Image.open(io.BytesIO(contents))
        if img.format not in ("JPEG", "PNG", "WEBP"):
            raise HTTPException(status_code=415, detail="JPEG, PNG, WEBP 형식만 지원합니다.")
        img.close()
    except UnidentifiedImageError:
        raise HTTPException(status_code=415, detail="이미지 파일이 아닙니다.")

    # 3. 업로드 디렉터리에 임시 저장 (UUID 파일명으로 원본 정보 노출 방지)
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = (file.filename or "upload").rsplit(".", 1)[-1].lower()
    if ext not in ("jpg", "jpeg", "png", "webp"):
        ext = "png"
    image_filename = f"{uuid.uuid4()}.{ext}"
    image_path = upload_dir / image_filename

    image_path.write_bytes(contents)

    # 4. 파서 호출
    parse_result = parser.parse(image_path, year, month)

    # 5. ScheduleMonth — 같은 (year, month)면 기존 row 사용
    schedule_month = db.query(ScheduleMonth).filter_by(year=year, month=month).first()
    if schedule_month is None:
        schedule_month = ScheduleMonth(year=year, month=month)
        db.add(schedule_month)
        db.flush()  # id 확보

    # 5-1. 같은 달의 '확정 안 한' 기존 버전(draft, reviewed) 정리
    #      확정본(applied)·버림(ignored)은 보존. 한 달에 작업본은 하나만 유지.
    stale_versions = (
        db.query(ScheduleVersion)
        .filter(
            ScheduleVersion.schedule_month_id == schedule_month.id,
            ScheduleVersion.status.in_([STATUS_DRAFT, STATUS_REVIEWED]),
        )
        .all()
    )
    for stale in stale_versions:
        if stale.source_image_path:
            stale_path = Path(stale.source_image_path)
            if stale_path.exists():
                stale_path.unlink()
        db.delete(stale)  # person/cell은 FK ondelete CASCADE로 함께 삭제
    if stale_versions:
        db.flush()

    # 6. ScheduleVersion 생성 (항상 새로 만듦)
    version = ScheduleVersion(
        schedule_month_id=schedule_month.id,
        status=STATUS_DRAFT,
        source_image_path=str(image_path),
    )
    db.add(version)
    db.flush()  # id 확보

    # 7. SchedulePerson rows 생성
    persons = []
    person_by_row: dict[int, SchedulePerson] = {}
    for p in parse_result.persons:
        person = SchedulePerson(
            schedule_version_id=version.id,
            table_type=table_type,
            name=p.name,
            row_index=p.row_index,
        )
        db.add(person)
        persons.append(person)
    db.flush()  # person id 확보

    for person in persons:
        person_by_row[person.row_index] = person

    # 8. ScheduleCell rows 생성
    cells = []
    for c in parse_result.cells:
        person = person_by_row.get(c.person_row_index)
        if person is None:
            continue
        cell = ScheduleCell(
            schedule_version_id=version.id,
            schedule_person_id=person.id,
            date=c.date,
            shift_code=c.shift_code,
            confidence_score=c.confidence_score,
            original_ocr_value=c.original_value,
            is_user_corrected=False,
        )
        db.add(cell)
        cells.append(cell)

    db.commit()
    db.refresh(version)
    db.refresh(schedule_month)
    for p in persons:
        db.refresh(p)
    for c in cells:
        db.refresh(c)

    return UploadResponse(
        version_id=version.id,
        status=version.status,
        schedule_month=ScheduleMonthOut.model_validate(schedule_month),
        table_type=table_type,
        created_at=version.created_at,
        updated_at=version.updated_at,
        persons=[PersonOut.model_validate(p) for p in persons],
        cells=[
            CellOut(
                cell_id=c.id,
                person_id=c.schedule_person_id,
                date=c.date,
                shift_code=c.shift_code,
                confidence_score=c.confidence_score,
                is_user_corrected=c.is_user_corrected,
                needs_review=(
                    c.confidence_score is not None
                    and c.confidence_score < CONFIDENCE_REVIEW_THRESHOLD
                ),
            )
            for c in cells
        ],
    )


def cancel_version(db: Session, version_id: int) -> None:
    version = db.query(ScheduleVersion).filter_by(id=version_id).first()
    if version is None:
        raise HTTPException(status_code=404, detail="버전을 찾을 수 없습니다.")
    if version.status != STATUS_DRAFT:
        raise HTTPException(status_code=409, detail="초안 상태인 버전만 취소할 수 있습니다.")

    # 이미지 파일 삭제
    if version.source_image_path:
        image_path = Path(version.source_image_path)
        if image_path.exists():
            image_path.unlink()

    # DB에서 버전 삭제 (cascade로 person, cell도 함께 삭제)
    db.delete(version)
    db.commit()
