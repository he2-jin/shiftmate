import pytest
from fastapi.testclient import TestClient

from app.db.models.schedule_cell import ScheduleCell
from app.db.models.schedule_month import ScheduleMonth
from app.db.models.schedule_person import SchedulePerson
from app.db.models.schedule_version import ScheduleVersion
from app.db.session import SessionLocal
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """각 테스트 후 생성된 데이터 정리 (테스트 격리)."""
    yield
    db = SessionLocal()
    try:
        db.query(ScheduleCell).delete()
        db.query(SchedulePerson).delete()
        db.query(ScheduleVersion).delete()
        db.query(ScheduleMonth).delete()
        db.commit()
    finally:
        db.close()
