from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import get_db
from app.parsers import get_parser
from app.schemas.schedule import (
    ApplyResponse,
    CellPatchRequest,
    CellPatchResponse,
    IgnoreResponse,
    ReviewResponse,
    UploadResponse,
    VersionDetailResponse,
)
from app.services.apply_service import apply_version, ignore_version
from app.services.review_service import complete_review, get_version_detail, patch_cell
from app.services.upload_service import cancel_version, upload_and_parse

router = APIRouter()


@router.post("/schedules/upload", response_model=UploadResponse, status_code=201)
def upload_schedule(
    image: UploadFile = File(..., description="근무표 이미지 (JPEG/PNG/WEBP)"),
    year: int = Form(..., ge=2020, le=2099, description="근무표 연도"),
    month: int = Form(..., ge=1, le=12, description="근무표 월"),
    table_type: str = Form(..., description="nursing_assistant 또는 support_staff"),
    db: Session = Depends(get_db),
):
    if table_type not in ("nursing_assistant", "support_staff"):
        raise HTTPException(status_code=422, detail="table_type은 nursing_assistant 또는 support_staff여야 합니다.")

    parser = get_parser(settings.parser_backend)
    return upload_and_parse(
        db=db,
        file=image,
        year=year,
        month=month,
        table_type=table_type,
        settings=settings,
        parser=parser,
    )


@router.delete("/schedules/versions/{version_id}", status_code=204)
def delete_version(
    version_id: int,
    db: Session = Depends(get_db),
):
    cancel_version(db=db, version_id=version_id)


@router.get("/schedules/versions/{version_id}", response_model=VersionDetailResponse)
def get_version(
    version_id: int,
    db: Session = Depends(get_db),
):
    return get_version_detail(db=db, version_id=version_id)


@router.patch("/schedules/cells/{cell_id}", response_model=CellPatchResponse)
def update_cell(
    cell_id: int,
    body: CellPatchRequest,
    db: Session = Depends(get_db),
):
    return patch_cell(db=db, cell_id=cell_id, shift_code=body.shift_code)


@router.post("/schedules/versions/{version_id}/review", response_model=ReviewResponse)
def review_version(
    version_id: int,
    db: Session = Depends(get_db),
):
    return complete_review(db=db, version_id=version_id)


@router.post("/schedules/versions/{version_id}/apply", response_model=ApplyResponse)
def apply_schedule_version(
    version_id: int,
    db: Session = Depends(get_db),
):
    return apply_version(db=db, version_id=version_id)


@router.post("/schedules/versions/{version_id}/ignore", response_model=IgnoreResponse)
def ignore_schedule_version(
    version_id: int,
    db: Session = Depends(get_db),
):
    return ignore_version(db=db, version_id=version_id)
