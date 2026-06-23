"""공유 링크 API 통합 테스트."""

from fastapi.testclient import TestClient

from app.db.models.schedule_cell import ScheduleCell
from app.db.models.schedule_month import ScheduleMonth
from app.db.models.schedule_person import SchedulePerson
from app.db.models.schedule_version import ScheduleVersion
from app.db.session import SessionLocal

import datetime as dt


def _setup_schedule(user_id: int) -> dict:
    """근무표·버전·근무자·셀 생성. person_id, month_id 반환."""
    db = SessionLocal()
    try:
        sm = ScheduleMonth(year=2026, month=6)
        db.add(sm)
        db.flush()

        version = ScheduleVersion(
            schedule_month_id=sm.id,
            status="applied",
        )
        db.add(version)
        db.flush()

        sm.active_version_id = version.id
        db.flush()

        person = SchedulePerson(
            schedule_version_id=version.id,
            table_type="nursing_assistant",
            name="테스트직원",
            row_index=0,
            user_id=user_id,
        )
        db.add(person)
        db.flush()

        cell = ScheduleCell(
            schedule_version_id=version.id,
            schedule_person_id=person.id,
            date=dt.date(2026, 6, 1),
            shift_code="D",
            confidence_score=0.99,
        )
        db.add(cell)
        db.commit()
        return {"month_id": sm.id, "person_id": person.id}
    finally:
        db.close()


def test_create_share_link(auth_client: TestClient):
    me = auth_client.get("/api/users/me").json()
    _setup_schedule(user_id=me["id"])

    resp = auth_client.post(
        "/api/shares", json={"year": 2026, "month": 6, "expires_in_days": 7}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "token" in data
    assert data["year"] == 2026
    assert data["month"] == 6


def test_create_share_replaces_existing(auth_client: TestClient):
    """같은 월 공유 링크 재생성 시 토큰이 바뀐다."""
    me = auth_client.get("/api/users/me").json()
    _setup_schedule(user_id=me["id"])

    r1 = auth_client.post(
        "/api/shares", json={"year": 2026, "month": 6, "expires_in_days": 7}
    )
    r2 = auth_client.post(
        "/api/shares", json={"year": 2026, "month": 6, "expires_in_days": 14}
    )
    assert r1.json()["token"] != r2.json()["token"]


def test_view_shared_schedule(auth_client: TestClient):
    me = auth_client.get("/api/users/me").json()
    _setup_schedule(user_id=me["id"])

    token = auth_client.post(
        "/api/shares", json={"year": 2026, "month": 6, "expires_in_days": 7}
    ).json()["token"]

    resp = auth_client.get(f"/api/shares/{token}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["person"]["name"] == "테스트직원"
    assert data["year"] == 2026
    assert len(data["cells"]) == 1


def test_view_shared_schedule_not_found(auth_client: TestClient):
    resp = auth_client.get("/api/shares/nonexistent-token")
    assert resp.status_code == 404


def test_view_shared_requires_login(client: TestClient):
    """비로그인 상태에서 공유 링크 조회 → 401/403."""
    resp = client.get("/api/shares/some-token")
    assert resp.status_code in (401, 403)


def test_delete_share_link(auth_client: TestClient):
    me = auth_client.get("/api/users/me").json()
    _setup_schedule(user_id=me["id"])

    token = auth_client.post(
        "/api/shares", json={"year": 2026, "month": 6, "expires_in_days": 7}
    ).json()["token"]

    resp = auth_client.delete(f"/api/shares/{token}")
    assert resp.status_code == 204

    # 삭제 후 조회 → 404
    assert auth_client.get(f"/api/shares/{token}").status_code == 404


def test_delete_share_only_owner(auth_client: TestClient, client: TestClient):
    """다른 사용자의 공유 링크 삭제 시도 → 403."""
    me = auth_client.get("/api/users/me").json()
    _setup_schedule(user_id=me["id"])

    token = auth_client.post(
        "/api/shares", json={"year": 2026, "month": 6, "expires_in_days": 7}
    ).json()["token"]

    # 다른 사용자로 로그인
    client.post("/api/auth/register", json={"email": "other2@test.com", "password": "otherpass123"})
    r = client.post("/api/auth/login", json={"email": "other2@test.com", "password": "otherpass123"})
    client.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})

    resp = client.delete(f"/api/shares/{token}")
    assert resp.status_code == 403


def test_create_share_no_schedule(auth_client: TestClient):
    """근무표 없는 달에 공유 링크 생성 → 404."""
    resp = auth_client.post(
        "/api/shares", json={"year": 2099, "month": 12, "expires_in_days": 7}
    )
    assert resp.status_code == 404
