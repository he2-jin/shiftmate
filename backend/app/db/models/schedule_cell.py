import datetime as dt

from sqlalchemy import Boolean, Date, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

SHIFT_D = "D"
SHIFT_E = "E"
SHIFT_N = "N"
SHIFT_OFF = "OFF"
SHIFT_LEAVE = "LEAVE"


class ScheduleCell(Base):
    __tablename__ = "schedule_cell"

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_version_id: Mapped[int] = mapped_column(
        ForeignKey("schedule_version.id", ondelete="CASCADE"), nullable=False
    )
    schedule_person_id: Mapped[int] = mapped_column(
        ForeignKey("schedule_person.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    shift_code: Mapped[str] = mapped_column(String(8), nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    original_ocr_value: Mapped[str | None] = mapped_column(String(32), nullable=True)
    corrected_value: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_user_corrected: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    __table_args__ = (
        UniqueConstraint(
            "schedule_version_id",
            "schedule_person_id",
            "date",
            name="uq_cell_version_person_date",
        ),
    )
