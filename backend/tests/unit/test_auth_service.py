"""auth_service 유닛 테스트 — 해싱·JWT 생성·검증."""

import time

from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_returns_hashed_string():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert len(hashed) > 20


def test_verify_password_correct():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("secret123")
    assert verify_password("wrong", hashed) is False


def test_create_access_token_decodable():
    token = create_access_token(user_id=1, email="a@b.com")
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["email"] == "a@b.com"


def test_create_refresh_token_decodable():
    token = create_refresh_token(user_id=1)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "1"


def test_decode_token_invalid_returns_none():
    assert decode_token("not.a.token") is None


def test_decode_token_expired_returns_none():
    from jose import jwt

    from app.config import settings

    # 이미 만료된 토큰 직접 생성
    payload = {"sub": "1", "exp": int(time.time()) - 1}
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    assert decode_token(token) is None
