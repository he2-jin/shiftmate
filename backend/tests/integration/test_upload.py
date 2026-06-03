import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image


def _make_png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color=(200, 200, 200)).save(buf, format="PNG")
    return buf.getvalue()


def test_upload_returns_201(client: TestClient):
    response = client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": "6", "table_type": "nursing_assistant"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    assert response.status_code == 201


def test_upload_response_has_required_fields(client: TestClient):
    response = client.post(
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


def test_upload_mock_returns_3_persons(client: TestClient):
    response = client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": "6", "table_type": "nursing_assistant"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    assert len(response.json()["persons"]) == 3


def test_upload_mock_returns_15_cells(client: TestClient):
    response = client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": "6", "table_type": "nursing_assistant"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    assert len(response.json()["cells"]) == 15


def test_upload_status_is_draft(client: TestClient):
    response = client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": "6", "table_type": "nursing_assistant"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    assert response.json()["status"] == "draft"


def test_upload_same_month_twice_increments_version(client: TestClient):
    kwargs = dict(
        data={"year": "2026", "month": "7", "table_type": "nursing_assistant"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    r1 = client.post("/api/schedules/upload", **kwargs)
    r2 = client.post("/api/schedules/upload", **kwargs)
    assert r1.status_code == 201
    assert r2.status_code == 201
    # 같은 month row를 공유하지만 version은 별개
    assert r1.json()["version_id"] != r2.json()["version_id"]
    assert r1.json()["schedule_month"]["id"] == r2.json()["schedule_month"]["id"]


def test_delete_version_returns_204(client: TestClient):
    r = client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": "8", "table_type": "support_staff"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    version_id = r.json()["version_id"]
    delete_r = client.delete(f"/api/schedules/versions/{version_id}")
    assert delete_r.status_code == 204


def test_delete_nonexistent_version_returns_404(client: TestClient):
    response = client.delete("/api/schedules/versions/99999")
    assert response.status_code == 404


def test_upload_invalid_table_type_returns_422(client: TestClient):
    response = client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": "6", "table_type": "invalid_type"},
        files={"image": ("test.png", _make_png_bytes(), "image/png")},
    )
    assert response.status_code == 422


def test_upload_text_file_returns_415(client: TestClient):
    response = client.post(
        "/api/schedules/upload",
        data={"year": "2026", "month": "6", "table_type": "nursing_assistant"},
        files={"image": ("test.txt", b"this is not an image", "text/plain")},
    )
    assert response.status_code == 415
