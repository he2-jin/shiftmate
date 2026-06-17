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
    client.post(f"/api/schedules/versions/{version_id}/review")
    client.post(f"/api/schedules/versions/{version_id}/apply")
    return version_id


def test_diff_shows_changed_cell(client: TestClient):
    active_id = _applied(client, month=1)

    # 같은 달에 새 작업본 업로드 (applied는 보존됨)
    up2 = _upload(client, month=1)
    v2 = up2["version_id"]

    # 새 작업본의 첫 칸을 확정본과 다른 값으로 수정
    cell = up2["cells"][0]
    new_code = "N" if cell["shift_code"] != "N" else "OFF"
    client.patch(f"/api/schedules/cells/{cell['cell_id']}", json={"shift_code": new_code})

    body = client.get(f"/api/schedules/versions/{v2}/diff").json()
    assert body["compared_to_version_id"] == active_id
    assert len(body["changes"]) == 1
    ch = body["changes"][0]
    assert ch["from_shift"] == cell["shift_code"]  # 확정본의 원래 값
    assert ch["to_shift"] == new_code


def test_diff_no_changes_when_identical(client: TestClient):
    _applied(client, month=2)
    up2 = _upload(client, month=2)  # 수정 없음 → 확정본과 동일(Mock)
    body = client.get(f"/api/schedules/versions/{up2['version_id']}/diff").json()
    assert body["changes"] == []


def test_diff_no_active_returns_empty(client: TestClient):
    # 확정본이 없는 달의 draft를 비교
    up = _upload(client, month=3)
    body = client.get(f"/api/schedules/versions/{up['version_id']}/diff").json()
    assert body["compared_to_version_id"] is None
    assert body["changes"] == []


def test_diff_version_not_found_404(client: TestClient):
    r = client.get("/api/schedules/versions/99999/diff")
    assert r.status_code == 404
