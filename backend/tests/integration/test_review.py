import io

from fastapi.testclient import TestClient
from PIL import Image


def _make_png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color=(200, 200, 200)).save(buf, format="PNG")
    return buf.getvalue()


def _upload(auth_client: TestClient, month: int = 6) -> dict:
    r = auth_client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": str(month), "table_type": "nursing_assistant"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    assert r.status_code == 201
    return r.json()


# ── 버전 조회 ──────────────────────────────────────────────────────

def test_get_version_returns_200(auth_client: TestClient):
    version_id = _upload(auth_client)["version_id"]
    r = auth_client.get(f"/api/schedules/versions/{version_id}")
    assert r.status_code == 200


def test_get_version_has_persons_and_cells(auth_client: TestClient):
    version_id = _upload(auth_client)["version_id"]
    body = auth_client.get(f"/api/schedules/versions/{version_id}").json()
    assert len(body["persons"]) == 3
    assert len(body["cells"]) == 15


def test_get_version_cell_has_cell_id(auth_client: TestClient):
    version_id = _upload(auth_client)["version_id"]
    cells = auth_client.get(f"/api/schedules/versions/{version_id}").json()["cells"]
    assert "cell_id" in cells[0]


def test_get_version_cell_has_needs_review(auth_client: TestClient):
    version_id = _upload(auth_client)["version_id"]
    cells = auth_client.get(f"/api/schedules/versions/{version_id}").json()["cells"]
    # Mock 파서 confidence_score는 0.9 이상 → needs_review = False
    assert all(c["needs_review"] is False for c in cells)


def test_get_version_not_found(auth_client: TestClient):
    r = auth_client.get("/api/schedules/versions/99999")
    assert r.status_code == 404


# ── 셀 수정 ──────────────────────────────────────────────────────

def test_patch_cell_returns_200(auth_client: TestClient):
    version_id = _upload(auth_client)["version_id"]
    cells = auth_client.get(f"/api/schedules/versions/{version_id}").json()["cells"]
    cell_id = cells[0]["cell_id"]
    r = auth_client.patch(f"/api/schedules/cells/{cell_id}", json={"shift_code": "E"})
    assert r.status_code == 200


def test_patch_cell_is_user_corrected(auth_client: TestClient):
    version_id = _upload(auth_client)["version_id"]
    cells = auth_client.get(f"/api/schedules/versions/{version_id}").json()["cells"]
    cell_id = cells[0]["cell_id"]
    body = auth_client.patch(f"/api/schedules/cells/{cell_id}", json={"shift_code": "N"}).json()
    assert body["is_user_corrected"] is True
    assert body["shift_code"] == "N"


def test_patch_cell_lowercase_normalized(auth_client: TestClient):
    """소문자 shift_code도 대문자로 정규화되어 저장."""
    version_id = _upload(auth_client)["version_id"]
    cells = auth_client.get(f"/api/schedules/versions/{version_id}").json()["cells"]
    cell_id = cells[0]["cell_id"]
    body = auth_client.patch(f"/api/schedules/cells/{cell_id}", json={"shift_code": "off"}).json()
    assert body["shift_code"] == "OFF"


def test_patch_cell_invalid_code_returns_422(auth_client: TestClient):
    version_id = _upload(auth_client)["version_id"]
    cells = auth_client.get(f"/api/schedules/versions/{version_id}").json()["cells"]
    cell_id = cells[0]["cell_id"]
    r = auth_client.patch(f"/api/schedules/cells/{cell_id}", json={"shift_code": "INVALID"})
    assert r.status_code == 422


def test_patch_cell_not_found(auth_client: TestClient):
    r = auth_client.patch("/api/schedules/cells/99999", json={"shift_code": "D"})
    assert r.status_code == 404


# ── 검토 완료 ──────────────────────────────────────────────────────

def test_review_returns_200(auth_client: TestClient):
    version_id = _upload(auth_client, month=9)["version_id"]
    r = auth_client.post(f"/api/schedules/versions/{version_id}/review")
    assert r.status_code == 200


def test_review_status_is_reviewed(auth_client: TestClient):
    version_id = _upload(auth_client, month=10)["version_id"]
    body = auth_client.post(f"/api/schedules/versions/{version_id}/review").json()
    assert body["status"] == "reviewed"
    assert body["reviewed_at"] is not None


def test_review_twice_returns_409(auth_client: TestClient):
    version_id = _upload(auth_client, month=11)["version_id"]
    auth_client.post(f"/api/schedules/versions/{version_id}/review")
    r = auth_client.post(f"/api/schedules/versions/{version_id}/review")
    assert r.status_code == 409


def test_review_not_found(auth_client: TestClient):
    r = auth_client.post("/api/schedules/versions/99999/review")
    assert r.status_code == 404


def test_get_version_after_review_shows_corrected_shift(auth_client: TestClient):
    """수정 후 조회 시 corrected_value가 반영됨."""
    version_id = _upload(auth_client, month=12)["version_id"]
    cells = auth_client.get(f"/api/schedules/versions/{version_id}").json()["cells"]
    cell_id = cells[0]["cell_id"]
    auth_client.patch(f"/api/schedules/cells/{cell_id}", json={"shift_code": "E"})
    cells_after = auth_client.get(f"/api/schedules/versions/{version_id}").json()["cells"]
    updated = next(c for c in cells_after if c["cell_id"] == cell_id)
    assert updated["shift_code"] == "E"
    assert updated["is_user_corrected"] is True
