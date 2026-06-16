import datetime as dt
from pathlib import Path

from PIL import Image

from app.parsers.base import ScheduleParser
from app.parsers.types import ParsedCell, ParsedPerson, ParseResult

# 고정 샘플 데이터 (테스트 재현성을 위해 랜덤 없음)
_MOCK_NAMES = ["김간호", "이지원", "박조무"]
_MOCK_SHIFTS = [
    ["D", "D", "N", "OFF", "E"],     # 김간호
    ["E", "D", "N", "LEAVE", "D"],   # 이지원
    ["N", "OFF", "D", "E", "N"],     # 박조무
]
_CONFIDENCE_SCORES = [0.97, 0.95, 0.98, 0.93, 0.96]


class MockScheduleParser(ScheduleParser):
    def parse(self, image_path: Path, year: int, month: int) -> ParseResult:
        # 이미지 파일이 진짜 이미지인지만 검증 (내용은 무시)
        with Image.open(image_path) as img:
            img.verify()

        persons = [
            ParsedPerson(name=name, row_index=i)
            for i, name in enumerate(_MOCK_NAMES)
        ]

        cells = []
        for row_idx, shifts in enumerate(_MOCK_SHIFTS):
            for day_idx, shift_code in enumerate(shifts):
                cells.append(ParsedCell(
                    person_row_index=row_idx,
                    date=dt.date(year, month, day_idx + 1),
                    shift_code=shift_code,
                    confidence_score=_CONFIDENCE_SCORES[day_idx],
                    original_value=shift_code,
                ))

        return ParseResult(persons=persons, cells=cells)
