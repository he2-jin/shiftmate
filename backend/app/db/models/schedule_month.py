import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

TABLE_TYPE_NURSING_ASSISTANT = "nursing_assistant"
TABLE_TYPE_SUPPORT_STAFF = "support_staff"


class ScheduleMonth(Base):
    __tablename__ = "schedule_month"

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    selected_table_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    selected_person_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "schedule_person.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_month_selected_person",
        ),
        nullable=True,
    )
    active_version_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "schedule_version.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_month_active_version",
        ),
        nullable=True,
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("year", "month", name="uq_schedule_month_year_month"),
    )
