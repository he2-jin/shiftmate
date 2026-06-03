import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

STATUS_DRAFT = "draft"
STATUS_REVIEWED = "reviewed"
STATUS_APPLIED = "applied"
STATUS_IGNORED = "ignored"


class ScheduleVersion(Base):
    __tablename__ = "schedule_version"

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_month_id: Mapped[int] = mapped_column(
        ForeignKey("schedule_month.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=STATUS_DRAFT
    )
    source_image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    image_deleted_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    parsed_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    applied_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "schedule_month_id", "version_number", name="uq_version_month_number"
        ),
    )
