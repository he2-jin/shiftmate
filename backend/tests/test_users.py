"""사용자 정보·근무자 연결 API 통합 테스트."""

import pytest
from fastapi.testclient import TestClient

from app.db.models.schedule_month import ScheduleMonth
from app.db.models.schedule_person import SchedulePerson
from app.db.models.schedule_version import ScheduleVersion
from app.db.session import SessionLocal


def _create_person(name: str, user_id: int | None = None) -> tuple[int, int]:
    """테스트용 근무표 + 근무자 생성. (month_id, person_id) 반환."""
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
            name=name,
            row_index=0,
            user_id=user_id,
        )
        db.add(person)
        db.commit()
        return sm.id, person.id
    finally:
        db.close()


def test_get_me(auth_client: TestClient):
    resp = auth_client.get("/api/users/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "testuser@test.com"
    assert data["is_active"] is True


def test_get_me_unauthorized(client: TestClient):
    resp = client.get("/api/users/me")
    assert resp.status_code in (401, 403)


def test_patch_me_person(auth_client: TestClient):
    _, person_id = _create_person("홍길동")
    resp = auth_client.patch("/api/users/me/person", json={"person_id": person_id})
    assert resp.status_code == 200


def test_patch_me_person_not_found(auth_client: TestClient):
    resp = auth_client.patch("/api/users/me/person", json={"person_id": 99999})
    assert resp.status_code == 404


def test_patch_me_person_conflict(auth_client: TestClient, client: TestClient):
    """다른 사용자가 이미 연결한 근무자에 연결 시도 → 409."""
    # 두 번째 사용자 생성
    client.post("/api/auth/register", json={"email": "other@test.com", "password": "otherpass123"})
    resp2 = client.post("/api/auth/login", json={"email": "other@test.com", "password": "otherpass123"})
    other_token = resp2.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {other_token}"})

    # 다른 사용자가 person에 연결
    _, person_id = _create_person("이순신")
    client.patch("/api/users/me/person", json={"person_id": person_id})

    # 첫 번째 사용자가 같은 person에 연결 시도
    resp = auth_client.patch("/api/users/me/person", json={"person_id": person_id})
    assert resp.status_code == 409


def test_get_my_schedule(auth_client: TestClient):
    # 로그인한 사용자의 user_id 확인
    me = auth_client.get("/api/users/me").json()
    _, person_id = _create_person("홍길동", user_id=me["id"])

    resp = auth_client.get("/api/users/me/schedules/2026/6")
    assert resp.status_code == 200
    data = resp.json()
    assert data["person"]["name"] == "홍길동"
    assert data["year"] == 2026
    assert data["month"] == 6


def test_get_my_schedule_no_link(auth_client: TestClient):
    """근무자 미연결 상태에서 내 근무 조회 → 404."""
    _create_person("김철수")  # 연결 없이 생성
    resp = auth_client.get("/api/users/me/schedules/2026/6")
    assert resp.status_code == 404


def test_get_my_schedule_no_active_version(auth_client: TestClient):
    """확정본 없는 달 → 404."""
    resp = auth_client.get("/api/users/me/schedules/2026/7")
    assert resp.status_code == 404
