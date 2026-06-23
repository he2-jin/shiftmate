"""셀 분할 엔진의 이미지→격자→근무표 전체 경로 회귀 테스트.

이전에 셀 분할 결과가 공통 전처리(흑백·확대·샤픈)와 좌표 재클러스터링을 거치며
망가지던(이름 'A 42', 코드 대부분 None) 버그를 막기 위한 검증.
격자를 OcrResult.grid로 흘려 parse가 좌표 재계산 없이 바로 매핑하는지 확인한다.

OpenCV/Tesseract가 없으면 건너뛴다.
"""

from pathlib import Path

import pytest

pytest.importorskip("cv2")
pytest.importorskip("pytesseract")
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from app.ocr.cell_split import CellSplitOcrEngine  # noqa: E402
from app.ocr.pipeline import process_schedule_image  # noqa: E402


def _font(size: int):
    for name in (
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def _make_grid_image(path: Path) -> None:
    """선이 또렷한 작은 근무표(헤더 + 한 사람)를 그린다."""
    cols = [10, 150, 260, 360, 450]
    rows = [10, 110, 230]
    img = Image.new("L", (460, 240), 255)
    d = ImageDraw.Draw(img)
    for x in cols:
        d.line([(x, rows[0]), (x, rows[-1])], fill=0, width=2)
    for y in rows:
        d.line([(cols[0], y), (cols[-1], y)], fill=0, width=2)

    grid_text = [["", "1", "2", "3"], ["Kim", "D", "N", "OFF"]]
    font = _font(40)
    for r in range(2):
        for c in range(4):
            t = grid_text[r][c]
            if not t:
                continue
            cx = (cols[c] + cols[c + 1]) // 2 - 18
            cy = (rows[r] + rows[r + 1]) // 2 - 22
            d.text((cx, cy), t, fill=0, font=font)
    img.save(path)


def test_cellsplit_pipeline_maps_grid_directly(tmp_path: Path):
    p = tmp_path / "grid.png"
    _make_grid_image(p)

    sched = process_schedule_image(p, engine=CellSplitOcrEngine())

    # 격자 경로를 탔는지 (좌표 재계산이 아니라 grid 직접 매핑)
    assert sched.ocr is not None and sched.ocr.grid is not None

    # 이름이 보존되고(이전 버그처럼 'A 42'로 깨지지 않음) 사람이 잡힌다
    assert len(sched.people) == 1
    person = sched.people[0]
    assert "Kim" in person.name

    # 단일 글자 코드는 OCR이 안정적 — 날짜→근무 매핑이 정확해야 한다
    codes = {d.day: d.code for d in person.days}
    assert codes.get(1) == "D"
    assert codes.get(2) == "N"
