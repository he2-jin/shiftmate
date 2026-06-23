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


def _merge_close_boundaries(bounds: list[int], min_gap: int | None = None) -> list[int]:
    """서로 너무 가까운 경계(글자를 선으로 오인한 가짜)를 하나로 합친다.

    진짜 표 선은 일정 간격으로 떨어져 있으므로, 정상 간격(중앙값)의 일부보다
    좁게 붙은 경계만 보수적으로 병합한다(멀리 떨어진 진짜 칸 경계는 건드리지 않음).
    """
    if len(bounds) < 2:
        return list(bounds)
    if min_gap is None:
        gaps = [bounds[i + 1] - bounds[i] for i in range(len(bounds) - 1)]
        median_gap = sorted(gaps)[len(gaps) // 2]
        min_gap = max(1, int(median_gap * 0.4))

    merged = [bounds[0]]
    for b in bounds[1:]:
        if b - merged[-1] < min_gap:
            merged[-1] = (merged[-1] + b) // 2  # 가까운 둘을 평균으로 합침
        else:
            merged.append(b)
    return merged


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
    return _merge_close_boundaries(bounds)


def _detect_cells(image_path: Path) -> tuple[np.ndarray | None, list[int], list[int]]:
    """격자선을 검출해 (회색조 이미지, 행 경계, 열 경계)를 돌려준다."""
    gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        return None, [], []
    bw = _binarize(gray)
    rows = _boundaries(_line_mask(bw, horizontal=True), axis=0)
    cols = _boundaries(_line_mask(bw, horizontal=False), axis=1)
    return gray, rows, cols


def detect_grid(image_path: Path) -> dict:
    """격자 경계만 검출(빠른 진단용). OCR은 하지 않는다."""
    gray, rows, cols = _detect_cells(image_path)
    if gray is None:
        return {"error": "이미지를 읽지 못함"}
    return {"shape": gray.shape, "row_bounds": rows, "col_bounds": cols}


def _recognize_cells(
    image_path: Path, lang: str = "kor+eng"
) -> tuple[list[list[str]], list[OcrWord]]:
    """격자를 셀별로 OCR해 (텍스트 2차원 격자, 위치가 담긴 OcrWord 목록)을 함께 돌려준다.

    격자 검출을 한 번만 수행하고, 같은 셀에서 격자 텍스트와 OcrWord를 동시에 만든다.
    얇은 열은 모든 행에서 동일하게 빠지므로 격자는 직사각형으로 유지된다.
    """
    gray, rows, cols = _detect_cells(image_path)
    grid: list[list[str]] = []
    words: list[OcrWord] = []
    if gray is None:
        return grid, words

    for r in range(len(rows) - 1):
        y0, y1 = rows[r], rows[r + 1]
        if y1 - y0 < 10:  # 너무 얇은 행 건너뜀
            continue
        row_cells: list[str] = []
        for c in range(len(cols) - 1):
            x0, x1 = cols[c], cols[c + 1]
            if x1 - x0 < 8:  # 너무 얇은 열 건너뜀(모든 행 동일)
                continue
            cell = gray[y0 + 2 : y1 - 2, x0 + 2 : x1 - 2]
            if cell.size == 0:
                row_cells.append("")
                continue
            text = pytesseract.image_to_string(cell, lang=lang, config="--psm 7").strip()
            row_cells.append(text)
            if text:
                words.append(
                    OcrWord(
                        text=text,
                        confidence=None,
                        bbox=BoundingBox(x=x0, y=y0, width=x1 - x0, height=y1 - y0),
                    )
                )
        if row_cells:
            grid.append(row_cells)
    return grid, words


def extract_grid(image_path: Path, lang: str = "kor+eng") -> list[list[str]]:
    """격자를 잘라 셀별로 OCR한 텍스트 2차원 배열을 돌려준다."""
    return _recognize_cells(image_path, lang)[0]


def extract_grid_words(image_path: Path, lang: str = "kor+eng") -> list[OcrWord]:
    """격자를 잘라 셀별로 OCR한 결과를 위치 정보가 담긴 OcrWord 목록으로 돌려준다."""
    return _recognize_cells(image_path, lang)[1]


class CellSplitOcrEngine(OcrEngine):
    """표 격자를 셀 단위로 잘라 OCR하는 엔진 (완전 로컬, 외부 전송 없음).

    자체 전처리(OpenCV 이진화)를 하므로 파이프라인 공통 전처리는 끈다.
    격자(grid)를 OcrResult에 담아 parse 단계가 좌표 재계산 없이 바로 매핑하게 한다.
    """

    needs_external_preprocess = False

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

        grid, words = _recognize_cells(image_path, self.lang)
        warnings = [] if grid else ["표 격자를 찾지 못했습니다."]
        return OcrResult(
            raw_text=raw_text, words=words, grid=grid or None, warnings=warnings
        )
