"""OCR이 읽은 글자(내용+위치)를 보고 근무표 구조로 맞추는 모듈.

빽빽한 표는 완벽히 맞추기 어렵다 — 위치 기반의 최선껏(best-effort) 복원이며,
애매한 부분은 normalize/validate 단계에서 경고로 드러난다.
"""

import re
import statistics

from app.ocr.normalize import normalize_shift_code
from app.ocr.schemas import (
    ExtractedDay,
    ExtractedPerson,
    ExtractedSchedule,
    OcrResult,
    OcrWord,
)

_YEAR_MONTH_RE = re.compile(r"(20\d{2})\s*년\s*(\d{1,2})\s*월")


def _extract_year_month(text: str) -> tuple[int | None, int | None]:
    m = _YEAR_MONTH_RE.search(text)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def _word_cx(w: OcrWord) -> float:
    return w.bbox.x + w.bbox.width / 2


def _word_cy(w: OcrWord) -> float:
    return w.bbox.y + w.bbox.height / 2


def _cluster_rows(words: list[OcrWord]) -> list[list[OcrWord]]:
    """비슷한 y 높이의 글자끼리 한 줄로 묶는다(가로줄 = 한 사람)."""
    located = [w for w in words if w.bbox is not None]
    if not located:
        return []

    tol = statistics.median(w.bbox.height for w in located) * 0.7
    located.sort(key=_word_cy)

    rows: list[list[OcrWord]] = []
    current: list[OcrWord] = []
    current_cy: float | None = None
    for w in located:
        cy = _word_cy(w)
        if current_cy is None or abs(cy - current_cy) <= tol:
            current.append(w)
            current_cy = cy if current_cy is None else (current_cy + cy) / 2
        else:
            rows.append(current)
            current = [w]
            current_cy = cy
    if current:
        rows.append(current)

    return [sorted(r, key=_word_cx) for r in rows]


def _find_date_header(rows: list[list[OcrWord]]) -> list[tuple[OcrWord, int]]:
    """1~31 숫자가 가장 많이 늘어선 줄을 날짜 헤더로 본다."""
    best: list[tuple[OcrWord, int]] = []
    for row in rows:
        nums = [
            (w, int(w.text))
            for w in row
            if w.text.isdigit() and 1 <= int(w.text) <= 31
        ]
        if len(nums) > len(best):
            best = nums
    return best


def _row_to_person(
    row: list[OcrWord], header: list[tuple[OcrWord, int]]
) -> ExtractedPerson | None:
    header_left = min(_word_cx(w) for w, _ in header)

    # 헤더 첫 날짜보다 왼쪽 글자 = 이름
    name_parts = [w.text for w in row if _word_cx(w) < header_left]
    name = " ".join(name_parts).strip()

    days: list[ExtractedDay] = []
    for date_word, day in header:
        col_x = _word_cx(date_word)
        # 이 날짜 열에서 가장 가까운(이름이 아닌) 글자를 그날 근무로 본다
        candidates = [w for w in row if _word_cx(w) >= header_left]
        if not candidates:
            continue
        nearest = min(candidates, key=lambda w: abs(_word_cx(w) - col_x))
        days.append(
            ExtractedDay(
                day=day,
                code=normalize_shift_code(nearest.text),
                confidence=nearest.confidence,
            )
        )

    has_code = any(d.code is not None for d in days)
    if not name and not has_code:
        return None
    return ExtractedPerson(name=name or "(이름 미상)", days=days)


def parse_schedule(ocr: OcrResult) -> ExtractedSchedule:
    """OCR 결과를 근무표 구조로 맞춘다."""
    year, month = _extract_year_month(ocr.raw_text)
    rows = _cluster_rows(ocr.words)
    header = _find_date_header(rows)

    people: list[ExtractedPerson] = []
    if header:
        header_cy = statistics.mean(_word_cy(w) for w, _ in header)
        for row in rows:
            if statistics.mean(_word_cy(w) for w in row) <= header_cy:
                continue  # 헤더 줄 및 그 위(제목 등)는 건너뜀
            person = _row_to_person(row, header)
            if person is not None:
                people.append(person)

    return ExtractedSchedule(
        source_type="shift_schedule",
        year=year,
        month=month,
        people=people,
        ocr=ocr,
    )
