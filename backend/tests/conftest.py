"""공통 pytest fixture — DB 정리, 기본 클라이언트, 인증 클라이언트."""

import pytest
from fastapi.testclient import TestClient

from app.db.models.ocr_correction import OcrCorrection
from app.db.models.schedule_cell import ScheduleCell
from app.db.models.schedule_month import ScheduleMonth
from app.db.models.schedule_person import SchedulePerson
from app.db.models.schedule_version import ScheduleVersion
from app.db.models.share_token import ShareToken
from app.db.models.user import User
from app.db.session import SessionLocal
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """비인증 TestClient — auth 엔드포인트 테스트용."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """각 테스트 후 생성된 데이터 정리 (테스트 격리)."""
    yield
    db = SessionLocal()
    try:
        db.query(ShareToken).delete()
        db.query(ScheduleCell).delete()
        db.query(SchedulePerson).delete()
        db.query(ScheduleVersion).delete()
        db.query(ScheduleMonth).delete()
        db.query(OcrCorrection).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def auth_client() -> TestClient:
    """인증된 TestClient — 기존 API 테스트에서 사용."""
    c = TestClient(app)
    c.post("/api/auth/register", json={"email": "testuser@test.com", "password": "testpass123"})
    resp = c.post("/api/auth/login", json={"email": "testuser@test.com", "password": "testpass123"})
    token = resp.json()["access_token"]
    c.headers.update({"Authorization": f"Bearer {token}"})
    return c
