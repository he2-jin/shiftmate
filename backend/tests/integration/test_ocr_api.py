import io

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw


def _text_image(text: str) -> bytes:
    img = Image.new("RGB", (600, 120), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 40), text, fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── OCR 처리 API ─────────────────────────────────────────────────────

def test_ocr_schedule_returns_structure(auth_client: TestClient):
    """실제 OCR을 거쳐 구조화된 응답을 돌려준다(정확도가 아니라 구조를 검증)."""
    r = auth_client.post(
        "/api/ocr/schedule",
        files={"image": ("t.png", _text_image("D E N OFF"), "image/png")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["source_type"] == "shift_schedule"
    assert "ocr" in body and "raw_text" in body["ocr"]
    assert "people" in body
    assert "warnings" in body
    assert "calendar_preview" in body


def test_ocr_schedule_handles_blank_image(auth_client: TestClient):
    """글자가 거의 없는 이미지도 에러 없이 경고와 함께 응답한다."""
    blank = Image.new("RGB", (200, 200), color="white")
    buf = io.BytesIO()
    blank.save(buf, format="PNG")
    r = auth_client.post(
        "/api/ocr/schedule",
        files={"image": ("blank.png", buf.getvalue(), "image/png")},
    )
    assert r.status_code == 200
    # 연/월을 못 읽으므로 경고가 있어야 한다
    assert len(r.json()["warnings"]) > 0


# ── 수정 기록 저장 API ───────────────────────────────────────────────

def test_ocr_correction_saved(auth_client: TestClient):
    body = {
        "original_code": "N",
        "original_confidence": 0.63,
        "corrected_code": "OFF",
        "target_date": "2026-06-12",
        "bbox": {"x": 120, "y": 340, "width": 50, "height": 30},
    }
    r = auth_client.post("/api/ocr/corrections", json=body)
    assert r.status_code == 201
    data = r.json()
    assert data["corrected_code"] == "OFF"
    assert "id" in data
    assert "created_at" in data


def test_ocr_correction_requires_corrected_code(auth_client: TestClient):
    r = auth_client.post("/api/ocr/corrections", json={"original_code": "N"})
    assert r.status_code == 422
