import io

from fastapi.testclient import TestClient
from PIL import Image


def _make_png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color=(200, 200, 200)).save(buf, format="PNG")
    return buf.getvalue()


def test_upload_returns_201(auth_client: TestClient):
    response = auth_client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": "6", "table_type": "nursing_assistant"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    assert response.status_code == 201


def test_upload_response_has_required_fields(auth_client: TestClient):
    response = auth_client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": "6", "table_type": "nursing_assistant"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    body = response.json()
    assert "version_id" in body
    assert "status" in body
    assert "schedule_month" in body
    assert "persons" in body
    assert "cells" in body


def test_upload_mock_returns_3_persons(auth_client: TestClient):
    response = auth_client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": "6", "table_type": "nursing_assistant"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    assert len(response.json()["persons"]) == 3


def test_upload_mock_returns_15_cells(auth_client: TestClient):
    response = auth_client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": "6", "table_type": "nursing_assistant"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    assert len(response.json()["cells"]) == 15


def test_upload_status_is_draft(auth_client: TestClient):
    response = auth_client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": "6", "table_type": "nursing_assistant"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    assert response.json()["status"] == "draft"


def _upload(auth_client: TestClient, month: int) -> dict:
    r = auth_client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": str(month), "table_type": "nursing_assistant"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    assert r.status_code == 201
    return r.json()


def test_reupload_same_month_replaces_previous_draft(auth_client: TestClient):
    """같은 달에 다시 올리면 이전 작업본(draft)은 사라지고 새 것만 남는다."""
    v1 = _upload(auth_client, month=7)["version_id"]
    v2 = _upload(auth_client, month=7)["version_id"]
    assert v1 != v2
    # 이전 draft는 삭제됨
    assert auth_client.get(f"/api/schedules/versions/{v1}").status_code == 404
    # 새 draft만 남음
    assert auth_client.get(f"/api/schedules/versions/{v2}").status_code == 200


def test_reupload_keeps_applied_version(auth_client: TestClient):
    """확정본(applied)이 있는 달에 새로 올려도 확정본은 보호된다."""
    v1 = _upload(auth_client, month=3)["version_id"]
    auth_client.post(f"/api/schedules/versions/{v1}/review")
    auth_client.post(f"/api/schedules/versions/{v1}/apply")

    _upload(auth_client, month=3)  # 같은 달 새 업로드

    detail = auth_client.get(f"/api/schedules/versions/{v1}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "applied"


def test_reupload_removes_reviewed_version(auth_client: TestClient):
    """확정 안 한 reviewed 버전도 새로 올리면 정리된다."""
    v1 = _upload(auth_client, month=4)["version_id"]
    auth_client.post(f"/api/schedules/versions/{v1}/review")  # reviewed (확정 안 함)

    _upload(auth_client, month=4)  # 같은 달 새 업로드

    assert auth_client.get(f"/api/schedules/versions/{v1}").status_code == 404


def test_delete_version_returns_204(auth_client: TestClient):
    r = auth_client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": "8", "table_type": "support_staff"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    version_id = r.json()["version_id"]
    delete_r = auth_client.delete(f"/api/schedules/versions/{version_id}")
    assert delete_r.status_code == 204


def test_delete_nonexistent_version_returns_404(auth_client: TestClient):
    response = auth_client.delete("/api/schedules/versions/99999")
    assert response.status_code == 404


def test_upload_invalid_table_type_returns_422(auth_client: TestClient):
    response = auth_client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": "6", "table_type": "invalid_type"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    assert response.status_code == 422


def test_upload_text_file_returns_415(auth_client: TestClient):
    response = auth_client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": "6", "table_type": "nursing_assistant"},
        files={"image": ("test.txt", b"this is not an image", "text/plain")},
    )
    assert response.status_code == 415
