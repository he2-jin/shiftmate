import io

from fastapi.testclient import TestClient
from PIL import Image


def _make_png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color=(200, 200, 200)).save(buf, format="PNG")
    return buf.getvalue()


def _upload(auth_client: TestClient, month: int) -> dict:
    r = auth_client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": str(month), "table_type": "nursing_assistant"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    assert r.status_code == 201
    return r.json()


def _reviewed_version(auth_client: TestClient, month: int) -> int:
    version_id = _upload(auth_client, month)["version_id"]
    r = auth_client.post(f"/api/schedules/versions/{version_id}/review")
    assert r.status_code == 200
    return version_id


# ── 확정(apply) ──────────────────────────────────────────────────────

def test_apply_returns_200(auth_client: TestClient):
    version_id = _reviewed_version(auth_client, month=1)
    r = auth_client.post(f"/api/schedules/versions/{version_id}/apply")
    assert r.status_code == 200


def test_apply_status_applied_and_applied_at(auth_client: TestClient):
    version_id = _reviewed_version(auth_client, month=2)
    body = auth_client.post(f"/api/schedules/versions/{version_id}/apply").json()
    assert body["status"] == "applied"
    assert body["applied_at"] is not None


def test_apply_sets_active_version(auth_client: TestClient):
    version_id = _reviewed_version(auth_client, month=3)
    body = auth_client.post(f"/api/schedules/versions/{version_id}/apply").json()
    assert body["active_version_id"] == version_id
    assert body["previous_active_version_id"] is None


def test_apply_from_draft_returns_409(auth_client: TestClient):
    # 검토하지 않은 draft 상태에서 바로 확정 시도
    version_id = _upload(auth_client, month=4)["version_id"]
    r = auth_client.post(f"/api/schedules/versions/{version_id}/apply")
    assert r.status_code == 409


def test_apply_not_found_returns_404(auth_client: TestClient):
    r = auth_client.post("/api/schedules/versions/99999/apply")
    assert r.status_code == 404


def test_reapply_demotes_previous_to_reviewed(auth_client: TestClient):
    """같은 달에 새 버전을 확정하면 기존 확정본은 reviewed로 되돌아간다."""
    first = _reviewed_version(auth_client, month=5)
    auth_client.post(f"/api/schedules/versions/{first}/apply")

    second = _reviewed_version(auth_client, month=5)
    body = auth_client.post(f"/api/schedules/versions/{second}/apply").json()

    assert body["active_version_id"] == second
    assert body["previous_active_version_id"] == first

    # 기존 확정본은 reviewed로 강등, applied_at 비워짐
    first_detail = auth_client.get(f"/api/schedules/versions/{first}").json()
    assert first_detail["status"] == "reviewed"


# ── 버리기(ignore) ───────────────────────────────────────────────────

def test_ignore_from_reviewed_returns_200_ignored(auth_client: TestClient):
    version_id = _reviewed_version(auth_client, month=8)
    r = auth_client.post(f"/api/schedules/versions/{version_id}/ignore")
    assert r.status_code == 200
    assert r.json()["status"] == "ignored"


def test_ignore_from_draft_ok(auth_client: TestClient):
    version_id = _upload(auth_client, month=9)["version_id"]
    r = auth_client.post(f"/api/schedules/versions/{version_id}/ignore")
    assert r.status_code == 200
    assert r.json()["status"] == "ignored"


def test_ignore_applied_returns_409(auth_client: TestClient):
    version_id = _reviewed_version(auth_client, month=10)
    auth_client.post(f"/api/schedules/versions/{version_id}/apply")
    r = auth_client.post(f"/api/schedules/versions/{version_id}/ignore")
    assert r.status_code == 409


def test_ignore_not_found_returns_404(auth_client: TestClient):
    r = auth_client.post("/api/schedules/versions/99999/ignore")
    assert r.status_code == 404


# ── 기존 기능 보호 (회귀) ────────────────────────────────────────────

def test_cancel_applied_returns_409(auth_client: TestClient):
    version_id = _reviewed_version(auth_client, month=6)
    auth_client.post(f"/api/schedules/versions/{version_id}/apply")
    r = auth_client.delete(f"/api/schedules/versions/{version_id}")
    assert r.status_code == 409


def test_review_applied_returns_409(auth_client: TestClient):
    version_id = _reviewed_version(auth_client, month=7)
    auth_client.post(f"/api/schedules/versions/{version_id}/apply")
    r = auth_client.post(f"/api/schedules/versions/{version_id}/review")
    assert r.status_code == 409
