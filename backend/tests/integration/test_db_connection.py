from sqlalchemy import text

from app.db.session import SessionLocal


def test_db_connection_returns_one() -> None:
    """PostgreSQL 컨테이너에 실제로 연결되어 간단한 SELECT가 동작하는지 확인."""
    with SessionLocal() as session:
        result = session.execute(text("SELECT 1")).scalar_one()

    assert result == 1


def test_models_register_in_metadata() -> None:
    """4개 모델이 Base.metadata에 등록되어 있는지 확인 (alembic autogenerate 전제 조건)."""
    from app.db.base import Base
    from app.db import models  # noqa: F401  # 모델들이 Base에 등록되도록 import

    table_names = set(Base.metadata.tables.keys())

    assert "schedule_month" in table_names
    assert "schedule_version" in table_names
    assert "schedule_person" in table_names
    assert "schedule_cell" in table_names
