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
    auth_client.post(f"/api/schedules/versions/{version_id}/review")
    auth_client.post(f"/api/schedules/versions/{version_id}/apply")
    return version_id


def test_diff_shows_changed_cell(auth_client: TestClient):
    active_id = _applied(auth_client, month=1)

    # 같은 달에 새 작업본 업로드 (applied는 보존됨)
    up2 = _upload(auth_client, month=1)
    v2 = up2["version_id"]

    # 새 작업본의 첫 칸을 확정본과 다른 값으로 수정
    cell = up2["cells"][0]
    new_code = "N" if cell["shift_code"] != "N" else "OFF"
    auth_client.patch(f"/api/schedules/cells/{cell['cell_id']}", json={"shift_code": new_code})

    body = auth_client.get(f"/api/schedules/versions/{v2}/diff").json()
    assert body["compared_to_version_id"] == active_id
    assert len(body["changes"]) == 1
    ch = body["changes"][0]
    assert ch["from_shift"] == cell["shift_code"]  # 확정본의 원래 값
    assert ch["to_shift"] == new_code


def test_diff_no_changes_when_identical(auth_client: TestClient):
    _applied(auth_client, month=2)
    up2 = _upload(auth_client, month=2)  # 수정 없음 → 확정본과 동일(Mock)
    body = auth_client.get(f"/api/schedules/versions/{up2['version_id']}/diff").json()
    assert body["changes"] == []


def test_diff_no_active_returns_empty(auth_client: TestClient):
    # 확정본이 없는 달의 draft를 비교
    up = _upload(auth_client, month=3)
    body = auth_client.get(f"/api/schedules/versions/{up['version_id']}/diff").json()
    assert body["compared_to_version_id"] is None
    assert body["changes"] == []


def test_diff_version_not_found_404(auth_client: TestClient):
    r = auth_client.get("/api/schedules/versions/99999/diff")
    assert r.status_code == 404
