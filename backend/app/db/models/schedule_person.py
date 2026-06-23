from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SchedulePerson(Base):
    __tablename__ = "schedule_person"

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_version_id: Mapped[int] = mapped_column(
        ForeignKey("schedule_version.id", ondelete="CASCADE"), nullable=False
    )
    table_type: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
