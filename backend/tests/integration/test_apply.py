import io

from fastapi.testclient import TestClient
from PIL import Image


def _make_png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color=(200, 200, 200)).save(buf, format="PNG")
    return buf.getvalue()


def _upload(client: TestClient, month: int) -> dict:
    r = client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": str(month), "table_type": "nursing_assistant"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    assert r.status_code == 201
    return r.json()


def _reviewed_version(client: TestClient, month: int) -> int:
    version_id = _upload(client, month)["version_id"]
    r = client.post(f"/api/schedules/versions/{version_id}/review")
    assert r.status_code == 200
    return version_id


# ── 확정(apply) ──────────────────────────────────────────────────────

def test_apply_returns_200(client: TestClient):
    version_id = _reviewed_version(client, month=1)
    r = client.post(f"/api/schedules/versions/{version_id}/apply")
    assert r.status_code == 200


def test_apply_status_applied_and_applied_at(client: TestClient):
    version_id = _reviewed_version(client, month=2)
    body = client.post(f"/api/schedules/versions/{version_id}/apply").json()
    assert body["status"] == "applied"
    assert body["applied_at"] is not None


def test_apply_sets_active_version(client: TestClient):
    version_id = _reviewed_version(client, month=3)
    body = client.post(f"/api/schedules/versions/{version_id}/apply").json()
    assert body["active_version_id"] == version_id
    assert body["previous_active_version_id"] is None


def test_apply_from_draft_returns_409(client: TestClient):
    # 검토하지 않은 draft 상태에서 바로 확정 시도
    version_id = _upload(client, month=4)["version_id"]
    r = client.post(f"/api/schedules/versions/{version_id}/apply")
    assert r.status_code == 409


def test_apply_not_found_returns_404(client: TestClient):
    r = client.post("/api/schedules/versions/99999/apply")
    assert r.status_code == 404


def test_reapply_demotes_previous_to_reviewed(client: TestClient):
    """같은 달에 새 버전을 확정하면 기존 확정본은 reviewed로 되돌아간다."""
    first = _reviewed_version(client, month=5)
    client.post(f"/api/schedules/versions/{first}/apply")

    second = _reviewed_version(client, month=5)
    body = client.post(f"/api/schedules/versions/{second}/apply").json()

    assert body["active_version_id"] == second
    assert body["previous_active_version_id"] == first

    # 기존 확정본은 reviewed로 강등, applied_at 비워짐
    first_detail = client.get(f"/api/schedules/versions/{first}").json()
    assert first_detail["status"] == "reviewed"


# ── 버리기(ignore) ───────────────────────────────────────────────────

def test_ignore_from_reviewed_returns_200_ignored(client: TestClient):
    version_id = _reviewed_version(client, month=8)
    r = client.post(f"/api/schedules/versions/{version_id}/ignore")
    assert r.status_code == 200
    assert r.json()["status"] == "ignored"


def test_ignore_from_draft_ok(client: TestClient):
    version_id = _upload(client, month=9)["version_id"]
    r = client.post(f"/api/schedules/versions/{version_id}/ignore")
    assert r.status_code == 200
    assert r.json()["status"] == "ignored"


def test_ignore_applied_returns_409(client: TestClient):
    version_id = _reviewed_version(client, month=10)
    client.post(f"/api/schedules/versions/{version_id}/apply")
    r = client.post(f"/api/schedules/versions/{version_id}/ignore")
    assert r.status_code == 409


def test_ignore_not_found_returns_404(client: TestClient):
    r = client.post("/api/schedules/versions/99999/ignore")
    assert r.status_code == 404


# ── 기존 기능 보호 (회귀) ────────────────────────────────────────────

def test_cancel_applied_returns_409(client: TestClient):
    version_id = _reviewed_version(client, month=6)
    client.post(f"/api/schedules/versions/{version_id}/apply")
    r = client.delete(f"/api/schedules/versions/{version_id}")
    assert r.status_code == 409


def test_review_applied_returns_409(client: TestClient):
    version_id = _reviewed_version(client, month=7)
    client.post(f"/api/schedules/versions/{version_id}/apply")
    r = client.post(f"/api/schedules/versions/{version_id}/review")
    assert r.status_code == 409
