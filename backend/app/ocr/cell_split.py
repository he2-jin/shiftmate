"""표의 격자선을 찾아 셀 단위로 잘라 OCR하는 실험 모듈.

통짜 OCR보다 정확도를 높이기 위한 접근:
선(가로/세로)을 검출 → 행/열 경계 추출 → 각 셀을 잘라 셀별로 OCR.
"""

from pathlib import Path

import cv2
import numpy as np
import pytesseract

from app.ocr.engine import OcrEngine
from app.ocr.schemas import BoundingBox, OcrResult, OcrWord


def _binarize(gray: np.ndarray) -> np.ndarray:
    return cv2.adaptiveThreshold(
        ~gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2
    )


def _line_mask(bw: np.ndarray, horizontal: bool, scale: int = 30) -> np.ndarray:
    if horizontal:
        size = max(1, bw.shape[1] // scale)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (size, 1))
    else:
        size = max(1, bw.shape[0] // scale)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, size))
    return cv2.dilate(cv2.erode(bw, kernel), kernel)


def _boundaries(mask: np.ndarray, axis: int, ratio: float = 0.4) -> list[int]:
    """선 마스크를 축으로 투영해 선이 모인 위치(경계)를 찾는다.

    axis=0 → 가로선의 y 위치(행 경계), axis=1 → 세로선의 x 위치(열 경계).
    """
    proj = mask.sum(axis=1) if axis == 0 else mask.sum(axis=0)
    if proj.max() == 0:
        return []
    threshold = proj.max() * ratio
    bounds: list[int] = []
    i, n = 0, len(proj)
    while i < n:
        if proj[i] > threshold:
            j = i
            while j < n and proj[j] > threshold:
                j += 1
            bounds.append((i + j) // 2)
            i = j
        else:
            i += 1
    return bounds


def detect_grid(image_path: Path) -> dict:
    """격자 경계만 검출(빠른 진단용). OCR은 하지 않는다."""
    gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        return {"error": "이미지를 읽지 못함"}
    bw = _binarize(gray)
    row_bounds = _boundaries(_line_mask(bw, horizontal=True), axis=0)
    col_bounds = _boundaries(_line_mask(bw, horizontal=False), axis=1)
    return {
        "shape": gray.shape,
        "row_bounds": row_bounds,
        "col_bounds": col_bounds,
    }


def extract_grid(image_path: Path, lang: str = "kor+eng") -> list[list[str]]:
    """격자를 잘라 셀별로 OCR한 텍스트 2차원 배열을 돌려준다."""
    gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    bw = _binarize(gray)
    rows = _boundaries(_line_mask(bw, horizontal=True), axis=0)
    cols = _boundaries(_line_mask(bw, horizontal=False), axis=1)

    grid: list[list[str]] = []
    for r in range(len(rows) - 1):
        y0, y1 = rows[r], rows[r + 1]
        if y1 - y0 < 10:  # 너무 얇은 행 건너뜀
            continue
        row_cells: list[str] = []
        for c in range(len(cols) - 1):
            x0, x1 = cols[c], cols[c + 1]
            if x1 - x0 < 8:
                continue
            cell = gray[y0 + 2 : y1 - 2, x0 + 2 : x1 - 2]
            if cell.size == 0:
                row_cells.append("")
                continue
            text = pytesseract.image_to_string(cell, lang=lang, config="--psm 7").strip()
            row_cells.append(text)
        if row_cells:
            grid.append(row_cells)
    return grid


def extract_grid_words(image_path: Path, lang: str = "kor+eng") -> list[OcrWord]:
    """격자를 잘라 셀별로 OCR한 결과를 위치 정보가 담긴 OcrWord 목록으로 돌려준다."""
    gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        return []
    bw = _binarize(gray)
    rows = _boundaries(_line_mask(bw, horizontal=True), axis=0)
    cols = _boundaries(_line_mask(bw, horizontal=False), axis=1)

    words: list[OcrWord] = []
    for r in range(len(rows) - 1):
        y0, y1 = rows[r], rows[r + 1]
        if y1 - y0 < 10:
            continue
        for c in range(len(cols) - 1):
            x0, x1 = cols[c], cols[c + 1]
            if x1 - x0 < 8:
                continue
            cell = gray[y0 + 2 : y1 - 2, x0 + 2 : x1 - 2]
            if cell.size == 0:
                continue
            text = pytesseract.image_to_string(cell, lang=lang, config="--psm 7").strip()
            if not text:
                continue
            words.append(
                OcrWord(
                    text=text,
                    confidence=None,
                    bbox=BoundingBox(x=x0, y=y0, width=x1 - x0, height=y1 - y0),
                )
            )
    return words


class CellSplitOcrEngine(OcrEngine):
    """표 격자를 셀 단위로 잘라 OCR하는 엔진 (완전 로컬, 외부 전송 없음)."""

    def __init__(self, lang: str = "kor+eng"):
        self.lang = lang

    def recognize(self, image_path: Path) -> OcrResult:
        from PIL import Image

        # 제목(연/월 등 표 밖 텍스트) 추출용 전체 OCR
        try:
            with Image.open(image_path) as img:
                raw_text = pytesseract.image_to_string(img, lang=self.lang)
        except Exception:  # noqa: BLE001
            raw_text = ""

        words = extract_grid_words(image_path, self.lang)
        warnings = [] if words else ["표 격자를 찾지 못했습니다."]
        return OcrResult(raw_text=raw_text, words=words, warnings=warnings)
