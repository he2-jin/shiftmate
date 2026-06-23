"""Auth API 통합 테스트 — 회원가입·로그인·갱신·로그아웃 흐름."""

from fastapi.testclient import TestClient


def test_register_success(client: TestClient):
    resp = client.post("/api/auth/register", json={"email": "a@test.com", "password": "pass1234"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "a@test.com"
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client: TestClient):
    payload = {"email": "dup@test.com", "password": "pass1234"}
    client.post("/api/auth/register", json=payload)
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 400


def test_register_short_password(client: TestClient):
    resp = client.post("/api/auth/register", json={"email": "b@test.com", "password": "short"})
    assert resp.status_code == 422


def test_login_success(client: TestClient):
    client.post("/api/auth/register", json={"email": "c@test.com", "password": "pass1234"})
    resp = client.post("/api/auth/login", json={"email": "c@test.com", "password": "pass1234"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    client.post("/api/auth/register", json={"email": "d@test.com", "password": "pass1234"})
    resp = client.post("/api/auth/login", json={"email": "d@test.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_login_unknown_email(client: TestClient):
    resp = client.post("/api/auth/login", json={"email": "nobody@test.com", "password": "pass1234"})
    assert resp.status_code == 401


def test_refresh_success(client: TestClient):
    client.post("/api/auth/register", json={"email": "e@test.com", "password": "pass1234"})
    login = client.post("/api/auth/login", json={"email": "e@test.com", "password": "pass1234"})
    refresh_token = login.json()["refresh_token"]

    resp = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_refresh_invalid_token(client: TestClient):
    resp = client.post("/api/auth/refresh", json={"refresh_token": "bad.token.here"})
    assert resp.status_code == 401


def test_logout_success(client: TestClient):
    client.post("/api/auth/register", json={"email": "f@test.com", "password": "pass1234"})
    login = client.post("/api/auth/login", json={"email": "f@test.com", "password": "pass1234"})
    access_token = login.json()["access_token"]

    resp = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 204


def test_logout_after_logout_refresh_fails(client: TestClient):
    """로그아웃 후 refresh token이 무효화되는지 확인."""
    client.post("/api/auth/register", json={"email": "g@test.com", "password": "pass1234"})
    login = client.post("/api/auth/login", json={"email": "g@test.com", "password": "pass1234"})
    tokens = login.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    resp = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 401
