import datetime as dt

from pydantic import BaseModel


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
    person_id: int
    date: dt.date
    shift_code: str
    confidence_score: float | None

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
