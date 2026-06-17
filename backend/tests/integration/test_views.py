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


def _applied(client: TestClient, month: int) -> int:
    version_id = _upload(client, month)["version_id"]
    assert client.post(f"/api/schedules/versions/{version_id}/review").status_code == 200
    assert client.post(f"/api/schedules/versions/{version_id}/apply").status_code == 200
    return version_id


# ── 월 전체 조회 ─────────────────────────────────────────────────────

def test_get_month_returns_200_when_applied(client: TestClient):
    _applied(client, month=1)
    r = client.get("/api/schedules/months/2026/1")
    assert r.status_code == 200


def test_get_month_has_persons_and_cells(client: TestClient):
    _applied(client, month=2)
    body = client.get("/api/schedules/months/2026/2").json()
    assert len(body["persons"]) == 3
    assert len(body["cells"]) == 15


def test_get_month_active_version_matches(client: TestClient):
    version_id = _applied(client, month=3)
    body = client.get("/api/schedules/months/2026/3").json()
    assert body["active_version_id"] == version_id


def test_get_month_no_active_returns_404(client: TestClient):
    # 업로드만 하고 확정하지 않음 → 확정본 없음
    _upload(client, month=4)
    r = client.get("/api/schedules/months/2026/4")
    assert r.status_code == 404


def test_get_month_nonexistent_returns_404(client: TestClient):
    r = client.get("/api/schedules/months/2099/1")
    assert r.status_code == 404


def test_get_month_reflects_corrected_cell(client: TestClient):
    version_id = _upload(client, month=5)["version_id"]
    cells = client.get(f"/api/schedules/versions/{version_id}").json()["cells"]
    cell_id = cells[0]["cell_id"]
    client.patch(f"/api/schedules/cells/{cell_id}", json={"shift_code": "E"})
    client.post(f"/api/schedules/versions/{version_id}/review")
    client.post(f"/api/schedules/versions/{version_id}/apply")

    body = client.get("/api/schedules/months/2026/5").json()
    updated = next(c for c in body["cells"] if c["cell_id"] == cell_id)
    assert updated["shift_code"] == "E"
    assert updated["is_user_corrected"] is True


# ── 개인별 조회 ──────────────────────────────────────────────────────

def test_get_person_returns_only_their_cells(client: TestClient):
    _applied(client, month=8)
    month_body = client.get("/api/schedules/months/2026/8").json()
    person_id = month_body["persons"][0]["id"]
    r = client.get(f"/api/schedules/months/2026/8/person/{person_id}")
    assert r.status_code == 200
    body = r.json()
    assert len(body["cells"]) == 5
    assert all(c["person_id"] == person_id for c in body["cells"])


def test_get_person_not_in_active_returns_404(client: TestClient):
    _applied(client, month=9)
    r = client.get("/api/schedules/months/2026/9/person/999999")
    assert r.status_code == 404


def test_get_person_nonexistent_month_404(client: TestClient):
    r = client.get("/api/schedules/months/2099/3/person/1")
    assert r.status_code == 404
