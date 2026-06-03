import datetime as dt

from pydantic import BaseModel

CONFIDENCE_REVIEW_THRESHOLD = 0.8


class ScheduleMonthOut(BaseModel):
    id: int
    year: int
    month: int

    model_config = {"from_attributes": True}


class PersonOut(BaseModel):
    id: int
    name: str
    row_index: int

    model_config = {"from_attributes": True}


class CellOut(BaseModel):
    cell_id: int
    person_id: int
    date: dt.date
    shift_code: str
    confidence_score: float | None
    is_user_corrected: bool
    needs_review: bool  # confidence_score < 0.8이면 True

    model_config = {"from_attributes": True}


class UploadResponse(BaseModel):
    version_id: int
    status: str
    schedule_month: ScheduleMonthOut
    table_type: str
    created_at: dt.datetime
    updated_at: dt.datetime
    persons: list[PersonOut]
    cells: list[CellOut]


class VersionDetailResponse(BaseModel):
    version_id: int
    status: str
    schedule_month: ScheduleMonthOut
    table_type: str
    created_at: dt.datetime
    updated_at: dt.datetime
    persons: list[PersonOut]
    cells: list[CellOut]


class CellPatchRequest(BaseModel):
    shift_code: str


class CellPatchResponse(BaseModel):
    cell_id: int
    person_id: int
    date: dt.date
    shift_code: str
    confidence_score: float | None
    is_user_corrected: bool
    needs_review: bool


class ReviewResponse(BaseModel):
    version_id: int
    status: str
    reviewed_at: dt.datetime
    image_deleted: bool
