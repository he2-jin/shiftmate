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


def _applied(auth_client: TestClient, month: int) -> int:
    version_id = _upload(auth_client, month)["version_id"]
    assert auth_client.post(f"/api/schedules/versions/{version_id}/review").status_code == 200
    assert auth_client.post(f"/api/schedules/versions/{version_id}/apply").status_code == 200
    return version_id


# ── 월 전체 조회 ─────────────────────────────────────────────────────

def test_get_month_returns_200_when_applied(auth_client: TestClient):
    _applied(auth_client, month=1)
    r = auth_client.get("/api/schedules/months/2026/1")
    assert r.status_code == 200


def test_get_month_has_persons_and_cells(auth_client: TestClient):
    _applied(auth_client, month=2)
    body = auth_client.get("/api/schedules/months/2026/2").json()
    assert len(body["persons"]) == 3
    assert len(body["cells"]) == 15


def test_get_month_active_version_matches(auth_client: TestClient):
    version_id = _applied(auth_client, month=3)
    body = auth_client.get("/api/schedules/months/2026/3").json()
    assert body["active_version_id"] == version_id


def test_get_month_no_active_returns_404(auth_client: TestClient):
    # 업로드만 하고 확정하지 않음 → 확정본 없음
    _upload(auth_client, month=4)
    r = auth_client.get("/api/schedules/months/2026/4")
    assert r.status_code == 404


def test_get_month_nonexistent_returns_404(auth_client: TestClient):
    r = auth_client.get("/api/schedules/months/2099/1")
    assert r.status_code == 404


def test_get_month_reflects_corrected_cell(auth_client: TestClient):
    version_id = _upload(auth_client, month=5)["version_id"]
    cells = auth_client.get(f"/api/schedules/versions/{version_id}").json()["cells"]
    cell_id = cells[0]["cell_id"]
    auth_client.patch(f"/api/schedules/cells/{cell_id}", json={"shift_code": "E"})
    auth_client.post(f"/api/schedules/versions/{version_id}/review")
    auth_client.post(f"/api/schedules/versions/{version_id}/apply")

    body = auth_client.get("/api/schedules/months/2026/5").json()
    updated = next(c for c in body["cells"] if c["cell_id"] == cell_id)
    assert updated["shift_code"] == "E"
    assert updated["is_user_corrected"] is True


# ── 개인별 조회 ──────────────────────────────────────────────────────

def test_get_person_returns_only_their_cells(auth_client: TestClient):
    _applied(auth_client, month=8)
    month_body = auth_client.get("/api/schedules/months/2026/8").json()
    person_id = month_body["persons"][0]["id"]
    r = auth_client.get(f"/api/schedules/months/2026/8/person/{person_id}")
    assert r.status_code == 200
    body = r.json()
    assert len(body["cells"]) == 5
    assert all(c["person_id"] == person_id for c in body["cells"])


def test_get_person_not_in_active_returns_404(auth_client: TestClient):
    _applied(auth_client, month=9)
    r = auth_client.get("/api/schedules/months/2026/9/person/999999")
    assert r.status_code == 404


def test_get_person_nonexistent_month_404(auth_client: TestClient):
    r = auth_client.get("/api/schedules/months/2099/3/person/1")
    assert r.status_code == 404
